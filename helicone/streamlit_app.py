import openai, streamlit as st
from langchain.llms.openai import OpenAI

openai.api_base = "https://oai.hconeai.com/v1"

# Streamlit app
st.subheader('LLM Observability Demo')

# Get OpenAI API key, Helicone API key, and user query
with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    helicone_api_key = st.text_input("Helicone API Key", type="password")
user_query = st.text_input("Your Query")

# If the 'Submit' button is clicked
if st.button("Submit"):
    # Validate inputs
    if not openai_api_key.strip() or not helicone_api_key.strip() or not user_query.strip():
        st.error(f"Please provide the missing fields.")
    else:
        try:
            with st.spinner('Please wait...'):
                # Initialize OpenAI model with Helicone integration
                llm = OpenAI(
                  temperature=0.9, 
                  openai_api_key=openai_api_key, 
                  headers={
                    "Helicone-Auth": f"Bearer {helicone_api_key}",
                    "Helicone-Cache-Enabled": "true"
                  }
                )
                
                # Run user query and display response
                st.success(llm(user_query))
        except Exception as e:
            st.error(f"An error occurred: {e}")
