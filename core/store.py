import os

import psycopg
import streamlit as st
from langchain_core.documents import Document
from langchain_postgres import Column, PGEngine, PGVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.llm import embeddings
from core.settings import EMBEDDING_SIZE

TABLE = "documents"


class StoreError(Exception):
    pass


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


def vectorstore() -> PGVectorStore:
    return PGVectorStore.create_sync(
        engine=_engine(_database_url()),
        embedding_service=embeddings(),
        table_name=TABLE,
        metadata_columns=["source", "page"],
    )


def add_documents(docs: list[Document]) -> int:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    chunks = [c for c in splitter.split_documents(docs) if c.page_content.strip()]
    if chunks:
        vectorstore().add_documents(chunks)
    return len(chunks)


def search(query: str, k: int = 6) -> list[Document]:
    return vectorstore().similarity_search(query, k=k)


def list_sources() -> list[tuple[str, int]]:
    url = _database_url()
    _engine(url)
    with psycopg.connect(url) as conn:
        rows = conn.execute(f'SELECT source, count(*) FROM "{TABLE}" GROUP BY source ORDER BY source').fetchall()
    return [(r[0], r[1]) for r in rows]


def delete_source(source: str) -> None:
    with psycopg.connect(_database_url()) as conn:
        conn.execute(f'DELETE FROM "{TABLE}" WHERE source = %s', (source,))
