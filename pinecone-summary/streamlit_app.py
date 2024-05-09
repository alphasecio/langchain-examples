import os, tempfile, streamlit as st
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import PyPDFLoader

# Streamlit app
st.subheader('Summarize Documents with LangChain & Pinecone')

# Sidebar for settings
with st.sidebar:
    st.subheader("Settings")
    openai_api_key = st.text_input("OpenAI API key", type="password")
    pinecone_api_key = st.text_input("Pinecone API key", type="password")
    pinecone_index = st.text_input("Pinecone index name")
source_doc = st.file_uploader("Source document", type="pdf")

# Set environment variables for API keys
os.environ['OPENAI_API_KEY'] = openai_api_key
os.environ['PINECONE_API_KEY'] = pinecone_api_key

if st.button("Summarize"):
    # Validate inputs
    if not openai_api_key or not pinecone_api_key or not pinecone_index or not source_doc:
        st.warning(f"Please upload the document and provide the missing fields.")
    else:
        try:
            with st.spinner("Please wait..."):
                # Save uploaded file temporarily to disk, load and split the file into pages, delete temp file
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                    tmp_file.write(source_doc.read())
                loader = PyPDFLoader(tmp_file.name)
                pages = loader.load_and_split()
                os.remove(tmp_file.name)
                
                # Create embeddings for the pages and insert into Pinecone vector database
                embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
                vectorstore = PineconeVectorStore.from_documents(pages, embeddings, index_name=pinecone_index)

                # Initialize the ChatOpenAI module, load and run the summarize chain
                llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)
                chain = load_summarize_chain(llm, chain_type="stuff")
                search = vectorstore.similarity_search(" ")
                summary = chain.run(input_documents=search, question="Write a concise summary within 200 words.")
                
                st.success(summary)
        except Exception as e:
            st.error(f"An error occurred: {e}")
