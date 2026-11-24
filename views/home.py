import streamlit as st

from core.settings import vector_store_label
from core.ui import footer, header

header(
    "🦜 LangChain Examples",
    "Four small apps built on LangChain, OpenAI and your choice of eight web search APIs.",
)

cards = [
    ("views/research.py", "🔎 Research Agent",
     "Ask a question. An agent searches the web, reads the best pages and answers with citations."),
    ("views/summarize.py", "📝 Summarize",
     "Paste text, drop in a URL or upload a PDF and get a short, detailed or bullet-point summary."),
    ("views/news.py", "📰 News Digest",
     "Pick a topic and a time window. Get the top stories, each summarized, plus a one-paragraph digest."),
    ("views/docs.py", "📚 Chat with Docs",
     f"Upload PDFs or text files into a {vector_store_label()} vector store and ask questions with cited answers."),
]

columns = st.columns(2)
for i, (page, title, text) in enumerate(cards):
    with columns[i % 2].container(border=True):
        st.subheader(title)
        st.write(text)
        st.page_link(page, label="Open", icon="➡️")

st.info("Add your OpenAI key and pick a search provider in the sidebar to get started.")
footer()
