# langchain-examples
<h4 align="center">
  <a href="https://github.com/alphasecio/langchain-examples/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="Released under the MIT license." />
  </a>
  <a href="https://github.com/alphasecio/langchain-examples">
    <img src="https://img.shields.io/github/stars/alphasecio/langchain-examples" alt="GitHub Stars" />
  </a>
  <a href="https://github.com/alphasecio/langchain-examples">
    <img src="https://img.shields.io/github/forks/alphasecio/langchain-examples" alt="GitHub Forks" />
  </a>
  <a href="https://github.com/alphasecio/langchain-examples">
    <img src="https://img.shields.io/github/watchers/alphasecio/langchain-examples" alt="GitHub Watchers" />
  </a>
  <a href="https://twitter.com/alphasecio">
    <img src="https://img.shields.io/twitter/follow/alphasecio?label=Follow" alt="Follow on Twitter" />
  </a>
</h4>

A single Streamlit app with four practical [LangChain](https://docs.langchain.com) tools, using OpenAI models, your choice of web search provider, and Postgres with pgvector for document storage.

| Tool | What it does |
| --- | --- |
| 🔎 **Web Research** | An agent that searches the web, reads pages and answers with cited sources. |
| 📝 **Summarize** | Summarizes pasted text, a web page or a PDF, as a short summary, a detailed one or bullet points. |
| 📰 **News Digest** | Finds top stories on any topic, summarizes each, and writes a one-paragraph digest. |
| 📚 **Chat with Docs** | Stores PDF, text and Markdown files in a Postgres vector store and answers questions with page-level citations. |

## Deploy

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/oE8sWo?referralCode=alphasec)

The template deploys the app and a Postgres database with pgvector. Add your OpenAI key and at least one search provider key, and you're ready. It also runs on any VPS with Docker and Postgres, such as a [DigitalOcean](https://m.do.co/c/5552e11c260f) droplet.

## Configuration

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | Yes | Postgres connection string. The pgvector extension and `documents` table are created on first use. |
| `OPENAI_API_KEY` | Yes | [OpenAI API key](https://platform.openai.com/api-keys). |
| `OPENAI_MODEL` | No | Default model, e.g. `gpt-6.1-terra`. Users can switch models in the sidebar. |
| `OPENAI_BASE_URL` | No | An OpenAI-compatible endpoint, if you don't call OpenAI directly. |
| `APP_PASSWORD` | No | Password required to open the app. See the note below. |
| `TAVILY_API_KEY` | No | [Tavily](https://app.tavily.com) |
| `EXA_API_KEY` | No | [Exa](https://dashboard.exa.ai) |
| `FIRECRAWL_API_KEY` | No | [Firecrawl](https://www.firecrawl.dev/referral?rid=XNXRER8X) |
| `PARALLEL_API_KEY` | No | [Parallel](https://platform.parallel.ai) |
| `PERPLEXITY_API_KEY` | No | [Perplexity](https://www.perplexity.ai/account/api) |
| `TINYFISH_API_KEY` | No | [TinyFish](https://agent.tinyfish.ai/sign-up) |
| `SERPER_API_KEY` | No | [Serper](https://serper.dev) |
| `SERPAPI_API_KEY` | No | [SerpApi](https://serpapi.com) |

Any key not set on the server can be entered in the sidebar instead. Keys entered there last only for that browser session and are never stored.

> [!IMPORTANT]
> **Set `APP_PASSWORD` if you put API keys on the server.** Without it, anyone who finds your app's URL can use your keys and spend your credits, and can read or delete documents in your library. If you leave the server keys empty and enter them in the sidebar instead, the app is safe to leave open.

## Run locally

```bash
docker run -d --name pgvector -e POSTGRES_PASSWORD=postgres -p 5432:5432 pgvector/pgvector:pg18
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
export OPENAI_API_KEY=...
streamlit run app.py
```

## Older examples

The earlier standalone apps (Chroma, Pinecone, Gemini, Helicone, SerpApi and others) are preserved on the [`legacy`](https://github.com/alphasecio/langchain-examples/tree/legacy) branch. They are no longer maintained.
