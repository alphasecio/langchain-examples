# langchain-pinecone-summary
A sample Streamlit web application for document summarization with LangChain and Pinecone.

[LangChain](https://langchain.readthedocs.io/en/latest) is an open-source framework created to aid the development of applications leveraging the power of large language models (LLMs). It can be used for chatbots, text summarisation, data generation, code understanding, question answering, evaluation, and more. [Pinecone](https://www.pinecone.io/), on the other hand, is a fully managed vector database, making it easy to build high-performance vector search applications without infrastructure hassles. Once you have generated the vector embeddings using a service like [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings), you can store, manage and search through them in Pinecone to power semantic search, recommendations, and other information retrieval use cases. See [this post](https://alphasec.io/langchain-decoded-part-2-embeddings/) on LangChain Embeddings for a primer on embeddings and sample use cases.

<img src="./../images/langchain-pinecone-summary.png" alt="langchain-pinecone-summary"/>

For a detailed tutorial on document summarization with LangChain and Pinecone, see [this post](https://alphasec.io/summarize-documents-with-langchain-and-pinecone).

To deploy on [Railway](https://railway.app/?referralCode=alphasec) using a one-click template, click the button below.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/Rg70kF?referralCode=alphasec)
