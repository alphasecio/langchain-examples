import os, tempfile, streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader

# Streamlit app config
st.subheader("Generative Q&A with LangChain, Gemini and Chroma")
with st.sidebar:
    google_api_key = st.text_input("Google API key", type="password")
    source_doc = st.file_uploader("Source document", type="pdf")
col1, col2 = st.columns([4,1])
query = col1.text_input("Query", label_visibility="collapsed")
os.environ['GOOGLE_API_KEY'] = google_api_key

# Session state initialization for documents and retrievers
if 'retriever' not in st.session_state or 'loaded_doc' not in st.session_state:
    st.session_state.retriever = None
    st.session_state.loaded_doc = None

submit = col2.button("Submit")

if submit:
    # Validate inputs
    if not google_api_key or not query:
        st.warning("Please provide the missing fields.")
    elif not source_doc:
        st.warning("Please upload the source document.")
    else:
        with st.spinner("Please wait..."):
            # Check if it's the same document; if not or if retriever isn't set, reload and recompute
            if st.session_state.loaded_doc != source_doc:
                try:
                    # Save uploaded file temporarily to disk, load and split the file into pages, delete temp file
                    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                        tmp_file.write(source_doc.read())
                    loader = PyPDFLoader(tmp_file.name)
                    pages = loader.load_and_split()
                    os.remove(tmp_file.name)
    
                    # Generate embeddings for the pages, and store in Chroma vector database
                    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
                    vectorstore = Chroma.from_documents(pages, embeddings)

                    #Configure Chroma as a retriever with top_k=5
                    st.session_state.retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
                    # Store the uploaded file in session state to prevent reloading
                    st.session_state.loaded_doc = source_doc
                except Exception as e:
                    st.error(f"An error occurred: {e}")
    
            try:
                # Initialize the ChatGoogleGenerativeAI module, create and invoke the retrieval chain
                llm = ChatGoogleGenerativeAI(model="gemini-pro")
                
                template = """
                You are a helpful AI assistant. Answer based on the context provided. 
                context: {context}
                input: {input}
                answer:
                """
                prompt = PromptTemplate.from_template(template)
                
                combine_docs_chain = create_stuff_documents_chain(llm, prompt)
                retrieval_chain = create_retrieval_chain(st.session_state.retriever, combine_docs_chain)
                response = retrieval_chain.invoke({"input": query})

                st.success(response['answer'])
            except Exception as e:
                st.error(f"An error occurred: {e}")
