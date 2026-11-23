import streamlit as st

from core import web
from core.summary import STYLES, summarize
from core.ui import footer, header, show_error

header("📝 Summarize", "Summarize pasted text, a web page or a PDF.")

source = st.segmented_control("Source", ["Text", "URL", "PDF"], default="Text")
style = st.segmented_control("Style", list(STYLES), default="Short")

text_input, url_input, pdf_input = "", "", None
if source == "Text":
    text_input = st.text_area("Text", height=250, placeholder="Paste the text to summarize")
elif source == "URL":
    url_input = st.text_input("URL", placeholder="https://")
else:
    pdf_input = st.file_uploader("PDF", type=["pdf"])

if st.button("Summarize", type="primary", disabled=not source or not style):
    try:
        with st.spinner("Summarizing…"):
            if source == "Text":
                text = text_input
            elif source == "URL":
                final_url, text = web.fetch_text(url_input)
                st.caption(f"Source: {final_url}")
            else:
                if not pdf_input:
                    raise ValueError("Upload a PDF first.")
                text = "\n\n".join(web.pdf_text(pdf_input.getvalue()))
            st.markdown(summarize(text, style))
    except Exception as e:
        show_error(e)

footer()
