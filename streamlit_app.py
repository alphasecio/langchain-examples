import os, tempfile
import streamlit as st, pinecone
from langchain.llms.openai import OpenAI
from langchain.vectorstores.pinecone import Pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import PyPDFLoader

# Streamlit app
st.subheader('Summarize Documents with LangChain & Pinecone')
            
# Get OpenAI API key, Pinecone API key, environment and index, and the source document input
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API key", type="password")
    pinecone_api_key = st.text_input("Pinecone API key", type="password")
    pinecone_env = st.text_input("Pinecone environment")
    pinecone_index = st.text_input("Pinecone index name")
source_doc = st.file_uploader("Upload source document", type="pdf", label_visibility="collapsed")

if st.button("Summarize"):
    # Validate inputs
    if not openai_api_key or not pinecone_api_key or not pinecone_env or not pinecone_index or not source_doc:
        st.warning(f"Please upload the document and provide the missing fields.")
    else:
        try:
            # Save uploaded file temporarily to disk, load and split the file into pages, delete temp file
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(source_doc.read())
            loader = PyPDFLoader(tmp_file.name)
            pages = loader.load_and_split()
            os.remove(tmp_file.name)
            
            # Create embeddings for the pages and insert into Pinecone vector database
            pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)
            embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
            vectordb = Pinecone.from_documents(pages, embeddings, index_name=pinecone_index)

            # Initialize the OpenAI module, load and run the summarize chain
            llm = OpenAI(temperature=0, openai_api_key=openai_api_key)
            chain = load_summarize_chain(llm, chain_type="stuff")
            search = vectordb.similarity_search(" ")
            summary = chain.run(input_documents=search, question="Write a concise summary within 200 words.")
            
            st.success(summary)
        except Exception as e:
            st.error(f"An error occurred: {e}")
