import os, tempfile
import streamlit as st
from langchain.llms.openai import OpenAI
from langchain.vectorstores.chroma import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import PyPDFLoader

# Set API keys from session state
openai_api_key = st.session_state.openai_api_key

# Streamlit app
st.subheader('Document Summary')
source_doc = st.file_uploader("Upload Source Document", type="pdf")

# If the 'Summarize' button is clicked
if st.button("Summarize"):
    # Validate inputs
    if not openai_api_key:
        st.error("Please provide the missing API keys in Settings.")
    elif not source_doc:
        st.error("Please provide the source document.")
    else:
        try:
            with st.spinner('Please wait...'):
              # Save uploaded file temporarily to disk, load and split the file into pages, delete temp file
              with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                  tmp_file.write(source_doc.read())
              loader = PyPDFLoader(tmp_file.name)
              pages = loader.load_and_split()
              os.remove(tmp_file.name)

              # Create embeddings for the pages and insert into Chroma database
              embeddings=OpenAIEmbeddings(openai_api_key=openai_api_key)
              vectordb = Chroma.from_documents(pages, embeddings)

              # Initialize the OpenAI module, load and run the summarize chain
              llm=OpenAI(temperature=0, openai_api_key=openai_api_key)
              chain = load_summarize_chain(llm, chain_type="stuff")
              search = vectordb.similarity_search(" ")
              summary = chain.run(input_documents=search, question="Write a summary within 200 words.")

              st.success(summary)
        except Exception as e:
            st.exception(f"An error occurred: {e}")
