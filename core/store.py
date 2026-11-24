"""Document library backed by Postgres/pgvector (default) or Pinecone.

Set VECTOR_STORE=pinecone to use Pinecone. Every function below keeps the same
signature in both modes, so the pages that call them don't need to know which
store is active.
"""

import base64
import os
import time
from collections import Counter
from collections.abc import Callable

import psycopg
import streamlit as st
from langchain_core.documents import Document
from langchain_postgres import Column, PGEngine, PGVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.llm import embeddings
from core.settings import EMBEDDING_SIZE, VECTOR_STORES, get_key, vector_store

TABLE = "documents"

PINECONE_DEFAULT_INDEX = "langchain-examples"
PINECONE_NAMESPACE = "library"
PINECONE_VECTOR_FIELD = "embedding"
PINECONE_CLOUD = "aws"
PINECONE_REGION = "us-east-1"
MAX_ENCODED_SOURCE = 480  # Pinecone IDs are at most 512 ASCII characters.


class StoreError(Exception):
    pass


def _backend() -> str:
    backend = vector_store()
    if backend not in VECTOR_STORES:
        raise StoreError(f"Unknown VECTOR_STORE '{backend}'. Use 'pgvector' or 'pinecone'.")
    return backend


def _split(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    return [c for c in splitter.split_documents(docs) if c.page_content.strip()]


# ---------------------------------------------------------------- pgvector


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise StoreError("DATABASE_URL is not set. Attach a Postgres (pgvector) database.")
    return url.replace("postgres://", "postgresql://", 1)


@st.cache_resource(show_spinner=False)
def _engine(url: str) -> PGEngine:
    engine = PGEngine.from_connection_string(url=url.replace("postgresql://", "postgresql+psycopg://", 1))
    with psycopg.connect(url) as conn:
        exists = conn.execute("SELECT to_regclass(%s)", (f"public.{TABLE}",)).fetchone()[0]
    if not exists:
        engine.init_vectorstore_table(
            table_name=TABLE,
            vector_size=EMBEDDING_SIZE,
            metadata_columns=[Column("source", "TEXT"), Column("page", "INTEGER")],
        )
    return engine


def _pg_vectorstore() -> PGVectorStore:
    return PGVectorStore.create_sync(
        engine=_engine(_database_url()),
        embedding_service=embeddings(),
        table_name=TABLE,
        metadata_columns=["source", "page"],
    )


def _pg_list_sources() -> list[tuple[str, int]]:
    url = _database_url()
    _engine(url)
    with psycopg.connect(url) as conn:
        rows = conn.execute(f'SELECT source, count(*) FROM "{TABLE}" GROUP BY source ORDER BY source').fetchall()
    return [(r[0], r[1]) for r in rows]


def _pg_delete_source(source: str) -> None:
    with psycopg.connect(_database_url()) as conn:
        conn.execute(f'DELETE FROM "{TABLE}" WHERE source = %s', (source,))


# ---------------------------------------------------------------- Pinecone
#
# Chunk IDs are "<source, URL-safe base64>#<chunk number>", so the Library list
# comes from listing IDs alone (no extra reads), and re-uploading a file with
# the same name overwrites its earlier chunks instead of duplicating them.


def _pinecone_errors(error: Exception) -> StoreError:
    from pinecone.errors.exceptions import (
        ForbiddenError,
        PaymentRequiredError,
        PineconeError,
        RateLimitError,
        UnauthorizedError,
    )

    if isinstance(error, (UnauthorizedError, ForbiddenError)):
        return StoreError("Pinecone rejected the API key.")
    if isinstance(error, PaymentRequiredError):
        return StoreError("Pinecone refused the request for this plan. Check your project's index limit.")
    if isinstance(error, RateLimitError):
        return StoreError("Pinecone rate limit reached; try again shortly.")
    if isinstance(error, PineconeError):
        return StoreError(f"Pinecone request failed: {str(error)[:300]}")
    return StoreError(str(error))


@st.cache_resource(show_spinner="Connecting to Pinecone…")
def _pinecone_index(api_key: str, name: str):
    from pinecone import Pinecone
    from pinecone.errors.exceptions import ConflictError, PineconeError

    pc = Pinecone(api_key=api_key)
    try:
        if not pc.indexes.exists(name):
            try:
                pc.indexes.create(
                    name=name,
                    schema={"fields": {PINECONE_VECTOR_FIELD: {
                        "type": "dense_vector", "dimension": EMBEDDING_SIZE, "metric": "cosine"}}},
                    deployment={"deployment_type": "managed", "cloud": PINECONE_CLOUD, "region": PINECONE_REGION},
                    timeout=300,
                )
            except ConflictError:
                pass  # Another session created it first.
        fields = getattr(pc.indexes.describe(name).schema, "fields", None) or {}
        field = fields.get(PINECONE_VECTOR_FIELD)
        if field is None or getattr(field, "dimension", None) != EMBEDDING_SIZE:
            raise StoreError(
                f"The Pinecone index '{name}' already exists with a different layout. "
                "Set PINECONE_INDEX to a new name and the app will create it."
            )
        return pc.index(name)
    except PineconeError as e:
        raise _pinecone_errors(e) from None


def _pinecone():
    key = get_key("PINECONE_API_KEY")
    if not key:
        raise StoreError("Add your Pinecone API key in the sidebar.")
    name = os.getenv("PINECONE_INDEX", "").strip() or PINECONE_DEFAULT_INDEX
    return _pinecone_index(key, name)


def _pinecone_call(fn: Callable):
    from pinecone.errors.exceptions import NotFoundError, PineconeError

    try:
        return fn()
    except NotFoundError:
        return None  # The namespace doesn't exist until the first upload.
    except PineconeError as e:
        raise _pinecone_errors(e) from None


def _id_prefix(source: str) -> str:
    encoded = base64.urlsafe_b64encode(source.encode()).decode().rstrip("=")
    if len(encoded) > MAX_ENCODED_SOURCE:
        raise StoreError("That file name is too long for Pinecone. Rename the file and try again.")
    return f"{encoded}#"


def _source_from_id(doc_id: str) -> str | None:
    encoded, sep, _ = doc_id.partition("#")
    if not sep:
        return None
    try:
        return base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode()
    except ValueError:
        return None


def _wait_until(check: Callable[[], bool], seconds: float = 15.0) -> None:
    """Pinecone applies writes asynchronously; wait briefly so the Library list is current."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.75)


def _pc_has_id(index, prefix: str) -> bool:
    first = _pinecone_call(lambda: next(iter(index.documents.list(namespace=PINECONE_NAMESPACE, prefix=prefix, limit=1)), None))
    return first is not None


def _pc_add(chunks: list[Document]) -> None:
    index = _pinecone()
    vectors = embeddings().embed_documents([c.page_content for c in chunks])
    counters: Counter = Counter()
    records = []
    for chunk, vector in zip(chunks, vectors):
        source = str(chunk.metadata.get("source") or "untitled")
        number = counters[source]
        counters[source] += 1
        records.append({
            "_id": f"{_id_prefix(source)}{number:06d}",
            PINECONE_VECTOR_FIELD: vector,
            "text": chunk.page_content,
            "source": source,
            "page": int(chunk.metadata.get("page") or 1),
        })
    result = _pinecone_call(lambda: index.documents.batch_upsert(
        namespace=PINECONE_NAMESPACE, documents=records, show_progress=False))
    if result is None:
        _pinecone_index.clear()
        raise StoreError("The Pinecone index was not found. Try again to recreate it.")
    if result.failed_item_count:
        raise StoreError(f"Pinecone rejected {result.failed_item_count} of {len(records)} chunks. Try again.")
    last = records[-1]["_id"]
    _wait_until(lambda: _pc_has_id(index, last))


def _pc_search(query: str, k: int) -> list[Document]:
    from pinecone import DenseVectorQuery

    index = _pinecone()
    vector = embeddings().embed_query(query)
    response = _pinecone_call(lambda: index.documents.search(
        namespace=PINECONE_NAMESPACE,
        top_k=k,
        score_by=[DenseVectorQuery(field=PINECONE_VECTOR_FIELD, values=vector)],
        include_fields=["text", "source", "page"],
    ))
    if response is None:
        return []
    return [
        Document(page_content=m.get("text") or "", metadata={"source": m.get("source"), "page": _page(m.get("page"))})
        for m in response.matches
    ]


def _page(value) -> int | None:
    # Pinecone stores numbers as floats, so 1 comes back as 1.0.
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _pc_list_sources() -> list[tuple[str, int]]:
    index = _pinecone()
    records = _pinecone_call(lambda: index.documents.list(namespace=PINECONE_NAMESPACE).to_list()) or []
    counts = Counter(s for s in (_source_from_id(r.id) for r in records) if s is not None)
    return sorted(counts.items())


def _pc_delete_source(source: str) -> None:
    index = _pinecone()
    _pinecone_call(lambda: index.documents.delete(namespace=PINECONE_NAMESPACE, filter={"source": {"$eq": source}}))
    prefix = _id_prefix(source)
    _wait_until(lambda: not _pc_has_id(index, prefix))


# ---------------------------------------------------------------- public API


def add_documents(docs: list[Document]) -> int:
    chunks = _split(docs)
    if chunks:
        if _backend() == "pinecone":
            _pc_add(chunks)
        else:
            _pg_vectorstore().add_documents(chunks)
    return len(chunks)


def search(query: str, k: int = 6) -> list[Document]:
    if _backend() == "pinecone":
        return _pc_search(query, k)
    return _pg_vectorstore().similarity_search(query, k=k)


def list_sources() -> list[tuple[str, int]]:
    if _backend() == "pinecone":
        return _pc_list_sources()
    return _pg_list_sources()


def delete_source(source: str) -> None:
    if _backend() == "pinecone":
        _pc_delete_source(source)
    else:
        _pg_delete_source(source)
