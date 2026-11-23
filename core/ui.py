import hmac
import os

import streamlit as st

from core.search import PROVIDERS
from core.settings import DIGITALOCEAN_URL, MODELS, RAILWAY_URL, REPO_URL, default_model, env_key


def require_password() -> None:
    password = os.getenv("APP_PASSWORD", "")
    if not password or st.session_state.get("authenticated"):
        return
    st.header("🦜 LangChain Examples")
    with st.form("login"):
        entered = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in", type="primary"):
            if hmac.compare_digest(entered.encode(), password.encode()):
                st.session_state.authenticated = True
                st.rerun()
            st.error("Incorrect password.")
    st.stop()


def _key_input(name: str, label: str, help_url: str) -> None:
    if env_key(name):
        st.caption(f"✓ {label} key set on the server")
        return
    st.text_input(f"{label} API key", type="password", key=f"key_{name}", help=f"Get a key: {help_url}")


def sidebar() -> None:
    models = MODELS if default_model() in MODELS else [default_model(), *MODELS]
    if "model" not in st.session_state:
        st.session_state.model = default_model()
    if "provider" not in st.session_state:
        configured = [p for p, v in PROVIDERS.items() if env_key(v.env)]
        st.session_state.provider = configured[0] if configured else "tavily"
    with st.sidebar:
        st.subheader("Settings")
        st.selectbox("Model", models, key="model")
        _key_input("OPENAI_API_KEY", "OpenAI", "https://platform.openai.com/api-keys")
        st.selectbox("Search provider", list(PROVIDERS), key="provider", format_func=lambda p: PROVIDERS[p].name)
        provider = PROVIDERS[st.session_state.provider]
        _key_input(provider.env, provider.name, provider.signup)
        if not os.getenv("APP_PASSWORD") and env_key("OPENAI_API_KEY"):
            st.warning("Server-side keys are set without APP_PASSWORD, so anyone with this URL can use them.")
        st.divider()
        st.caption("Keys entered here stay in your browser session and are never stored.")


def header(title: str, description: str) -> None:
    st.header(title)
    st.caption(description)


def footer() -> None:
    st.divider()
    st.caption(
        f"Open source on [GitHub]({REPO_URL}) · Runs on [Railway]({RAILWAY_URL}) "
        f"or any VPS, such as [DigitalOcean]({DIGITALOCEAN_URL}) · Built by [alphasec](https://alphasec.io)"
    )


def show_error(error: Exception) -> None:
    st.error(str(error) or error.__class__.__name__)
