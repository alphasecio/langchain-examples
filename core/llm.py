import os

import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from core.settings import EMBEDDING_MODEL, get_key


class MissingKey(Exception):
    pass


def _openai_key() -> str:
    key = get_key("OPENAI_API_KEY")
    if not key:
        raise MissingKey("Add your OpenAI API key in the sidebar.")
    return key


def chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=st.session_state.get("model", ""),
        api_key=_openai_key(),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        timeout=120,
        max_retries=2,
    )


def embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=_openai_key())


def ask(prompt: str) -> str:
    return chat_model().invoke(prompt).text
