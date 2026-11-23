import streamlit as st

from core.ui import require_password, sidebar

st.set_page_config(page_title="LangChain Examples", page_icon="🦜", layout="wide")
require_password()

pages = [
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("views/research.py", title="Research Agent", icon="🔎", url_path="research"),
    st.Page("views/summarize.py", title="Summarize", icon="📝", url_path="summarize"),
    st.Page("views/news.py", title="News Digest", icon="📰", url_path="news"),
    st.Page("views/docs.py", title="Chat with Docs", icon="📚", url_path="docs"),
]

navigation = st.navigation(pages)
sidebar()
navigation.run()
