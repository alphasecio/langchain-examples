import os, streamlit as st
from langchain.utilities.tavily_search import TavilySearchAPIWrapper
from langchain.agents import initialize_agent, AgentType
from langchain_community.chat_models import ChatOpenAI
from langchain.tools.tavily_search import TavilySearchResults

# Streamlit app
st.subheader('LangChain Search with Tavily')
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API key", value="", type="password")
    st.caption("*If you don't have an OpenAI API key, get it [here](https://platform.openai.com/account/api-keys).*")
    tavily_api_key = st.text_input("Tavily API Key", type="password")
    st.caption("*If you don't have a Tavily API key, get it [here](https://tavily.com/#api).*")
search_query = st.text_input("Search Query", label_visibility="collapsed")
os.environ["TAVILY_API_KEY"] = tavily_api_key

# If the 'Search' button is clicked
if st.button("Search"):
    if not openai_api_key.strip() or not tavily_api_key.strip() or not search_query.strip():
        st.error(f"Please provide the missing fields.")
    else:
        try:
            with st.spinner('Please wait...'):
                llm = ChatOpenAI(temperature=0.7, openai_api_key=openai_api_key)
                search = TavilySearchAPIWrapper()
                tavily_tool = TavilySearchResults(api_wrapper=search, tavily_api_key=tavily_api_key)

                agent_chain = initialize_agent(
                    [tavily_tool],
                    llm,
                    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
                    verbose=True,
                )

                result = agent_chain.run({"input": search_query})
                st.success(result)
        except Exception as e:
            st.exception(f"An error occurred: {e}")
