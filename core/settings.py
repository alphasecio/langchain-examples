import os

import streamlit as st

MODELS = ["gpt-6.1-terra", "gpt-6-luna", "gpt-6.2-sol"]
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_SIZE = 1536

RAILWAY_URL = "https://railway.com/?referralCode=alphasec"
DIGITALOCEAN_URL = "https://m.do.co/c/5552e11c260f"
REPO_URL = "https://github.com/alphasecio/langchain-examples"


def env_key(name: str) -> str:
    return os.getenv(name, "").strip()


def get_key(name: str) -> str:
    return st.session_state.get(f"key_{name}", "").strip() or env_key(name)


VECTOR_STORES = {"pgvector": "Postgres", "pinecone": "Pinecone"}


def vector_store() -> str:
    """The configured vector store: VECTOR_STORE=pgvector (default) or pinecone."""
    return env_key("VECTOR_STORE").lower() or "pgvector"


def vector_store_label() -> str:
    return VECTOR_STORES.get(vector_store(), vector_store())


def default_model() -> str:
    model = env_key("OPENAI_MODEL")
    return model if model else MODELS[0]
