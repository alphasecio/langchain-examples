import streamlit as st, tiktoken
from langchain.chat_models import ChatOpenAI
from langchain.utilities import GoogleSerperAPIWrapper
from langchain.document_loaders import UnstructuredURLLoader
from langchain.chains.summarize import load_summarize_chain

# Streamlit app
st.subheader('Last Week In...')

# Get OpenAI API key, Serper API key, number of results, and search query
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", value="", type="password")
    serper_api_key = st.text_input("Serper API Key", value="", type="password")
    num_results = st.number_input("Number of Search Results", min_value=3, max_value=10)
    st.caption("*Search: Uses Serper API only, retrieves search results.*")
    st.caption("*Search & Summarize: Uses Serper & OpenAI APIs, summarizes each search result.*")
search_query = st.text_input("Search Query", label_visibility="collapsed")
col1, col2 = st.columns(2)

# If the 'Search' button is clicked
if col1.button("Search"):
    # Validate inputs
    if not openai_api_key.strip() or not serper_api_key.strip() or not search_query.strip():
        st.error(f"Please provide the missing fields.")
    else:
        try:
            with st.spinner("Please wait..."):
                # Show the top X relevant news articles from the previous week using Google Serper API
                search = GoogleSerperAPIWrapper(type="news", tbs="qdr:w1", serper_api_key=serper_api_key)
                result_dict = search.results(search_query)

                if not result_dict['news']:
                    st.error(f"No search results for: {search_query}.")
                else:
                    for i, item in zip(range(num_results), result_dict['news']):
                        st.success(f"Title: {item['title']}\n\nLink: {item['link']}\n\nSnippet: {item['snippet']}")
        except Exception as e:
            st.exception(f"Exception: {e}")

# If 'Search & Summarize' button is clicked
if col2.button("Search & Summarize"):
    # Validate inputs
    if not openai_api_key.strip() or not serper_api_key.strip() or not search_query.strip():
        st.error(f"Please provide the missing fields.")
    else:
        try:
            with st.spinner("Please wait..."):
                # Show the top X relevant news articles from the previous week using Google Serper API
                search = GoogleSerperAPIWrapper(type="news", tbs="qdr:w1", serper_api_key=serper_api_key)
                result_dict = search.results(search_query)

                if not result_dict['news']:
                    st.error(f"No search results for: {search_query}.")
                else:
                    # Load URL data from the top X news search results
                    for i, item in zip(range(num_results), result_dict['news']):
                        loader = UnstructuredURLLoader(urls=[item['link']])
                        data = loader.load()

                        # Initialize the ChatOpenAI module, load and run the summarize chain
                        llm = ChatOpenAI(temperature=0, model='gpt-3.5-turbo', openai_api_key=openai_api_key)
                        chain = load_summarize_chain(llm, chain_type="map_reduce")
                        summary = chain.run(data)

                        st.success(f"Title: {item['title']}\n\nLink: {item['link']}\n\nSummary: {summary}")
        except Exception as e:
            st.exception(f"Exception: {e}")
