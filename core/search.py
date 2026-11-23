from dataclasses import dataclass
from datetime import date, timedelta

import httpx

from core.settings import get_key

TIMEOUT = httpx.Timeout(30.0)
WINDOWS = {"Past day": 1, "Past week": 7, "Past month": 30}


@dataclass
class Result:
    title: str
    url: str
    snippet: str
    date: str = ""


@dataclass
class Provider:
    name: str
    env: str
    signup: str


PROVIDERS = {
    "tavily": Provider("Tavily", "TAVILY_API_KEY", "https://app.tavily.com"),
    "exa": Provider("Exa", "EXA_API_KEY", "https://dashboard.exa.ai"),
    "firecrawl": Provider("Firecrawl", "FIRECRAWL_API_KEY", "https://www.firecrawl.dev/referral?rid=XNXRER8X"),
    "parallel": Provider("Parallel", "PARALLEL_API_KEY", "https://platform.parallel.ai"),
    "perplexity": Provider("Perplexity", "PERPLEXITY_API_KEY", "https://www.perplexity.ai/account/api"),
    "tinyfish": Provider("TinyFish", "TINYFISH_API_KEY", "https://agent.tinyfish.ai/sign-up"),
    "serper": Provider("Serper", "SERPER_API_KEY", "https://serper.dev"),
    "serpapi": Provider("SerpApi", "SERPAPI_API_KEY", "https://serpapi.com"),
}


class SearchError(Exception):
    pass


def _since(days: int) -> str:
    return (date.today() - timedelta(days=days)).isoformat()


def _tbs(days: int) -> str:
    return {1: "qdr:d", 7: "qdr:w", 30: "qdr:m"}.get(days, "qdr:w")


def _send(provider: str, method: str, url: str, **kwargs) -> dict:
    try:
        response = httpx.request(method, url, timeout=TIMEOUT, **kwargs)
    except httpx.HTTPError:
        raise SearchError(f"Could not reach {PROVIDERS[provider].name}.") from None
    if response.status_code in (401, 403):
        raise SearchError(f"{PROVIDERS[provider].name} rejected the API key.")
    if response.status_code == 429:
        raise SearchError(f"{PROVIDERS[provider].name} rate limit reached; try again shortly.")
    if response.status_code >= 400:
        raise SearchError(f"{PROVIDERS[provider].name} returned HTTP {response.status_code}.")
    return response.json()


def _tavily(key, query, n, news, days):
    body = {"query": query, "max_results": n, "topic": "news" if news else "general"}
    if days:
        body["time_range"] = {1: "day", 7: "week", 30: "month"}.get(days, "week")
    data = _send("tavily", "POST", "https://api.tavily.com/search", json=body,
                 headers={"Authorization": f"Bearer {key}"})
    return [Result(r.get("title", ""), r.get("url", ""), r.get("content", ""), r.get("published_date") or "")
            for r in data.get("results", [])]


def _exa(key, query, n, news, days):
    body = {"query": query, "numResults": n, "type": "auto", "contents": {"text": {"maxCharacters": 1500}}}
    if news:
        body["category"] = "news"
    if days:
        body["startPublishedDate"] = f"{_since(days)}T00:00:00.000Z"
    data = _send("exa", "POST", "https://api.exa.ai/search", json=body, headers={"x-api-key": key})
    return [Result(r.get("title") or "", r.get("url", ""), r.get("text") or "", (r.get("publishedDate") or "")[:10])
            for r in data.get("results", [])]


def _firecrawl(key, query, n, news, days):
    body = {"query": query, "limit": n, "sources": [{"type": "news" if news else "web"}]}
    if days:
        body["tbs"] = _tbs(days)
    data = _send("firecrawl", "POST", "https://api.firecrawl.dev/v2/search", json=body,
                 headers={"Authorization": f"Bearer {key}"}).get("data", {})
    items = data.get("news" if news else "web", [])
    return [Result(r.get("title", ""), r.get("url", ""), r.get("snippet") or r.get("description") or "", r.get("date") or "")
            for r in items]


def _parallel(key, query, n, news, days):
    settings = {"max_results": n, "excerpt_settings": {"max_chars_per_result": 1500}}
    if days:
        settings["source_policy"] = {"after_date": _since(days)}
    body = {"objective": query, "search_queries": [query], "mode": "basic", "advanced_settings": settings}
    data = _send("parallel", "POST", "https://api.parallel.ai/v1/search", json=body, headers={"x-api-key": key})
    return [Result(r.get("title") or "", r.get("url", ""), "\n".join(r.get("excerpts") or []), r.get("publish_date") or "")
            for r in data.get("results", [])]


def _perplexity(key, query, n, news, days):
    body = {"query": query, "max_results": min(n, 20)}
    if days:
        body["search_recency_filter"] = {1: "day", 7: "week", 30: "month"}.get(days, "week")
    data = _send("perplexity", "POST", "https://api.perplexity.ai/search", json=body,
                 headers={"Authorization": f"Bearer {key}"})
    return [Result(r.get("title", ""), r.get("url", ""), r.get("snippet", ""), r.get("date") or "")
            for r in data.get("results", [])][:n]


def _tinyfish(key, query, n, news, days):
    params = {"query": query}
    if news:
        params["domain_type"] = "news"
    if days:
        params["recency_minutes"] = days * 1440
    data = _send("tinyfish", "GET", "https://api.search.tinyfish.ai", params=params, headers={"X-API-Key": key})
    return [Result(r.get("title", ""), r.get("url", ""), r.get("snippet", ""), r.get("date") or "")
            for r in data.get("results", [])][:n]


def _serper(key, query, n, news, days):
    body = {"q": query, "num": n}
    if days:
        body["tbs"] = _tbs(days)
    endpoint = "news" if news else "search"
    data = _send("serper", "POST", f"https://google.serper.dev/{endpoint}", json=body, headers={"X-API-KEY": key})
    items = data.get("news" if news else "organic", [])
    return [Result(r.get("title", ""), r.get("link", ""), r.get("snippet", ""), r.get("date") or "")
            for r in items][:n]


def _serpapi(key, query, n, news, days):
    params = {"engine": "google", "q": query, "num": n, "api_key": key}
    if news:
        params["tbm"] = "nws"
    if days:
        params["tbs"] = _tbs(days)
    data = _send("serpapi", "GET", "https://serpapi.com/search.json", params=params)
    items = data.get("news_results" if news else "organic_results", [])
    return [Result(r.get("title", ""), r.get("link", ""), r.get("snippet", ""), r.get("date") or "")
            for r in items][:n]


ADAPTERS = {
    "tavily": _tavily,
    "exa": _exa,
    "firecrawl": _firecrawl,
    "parallel": _parallel,
    "perplexity": _perplexity,
    "tinyfish": _tinyfish,
    "serper": _serper,
    "serpapi": _serpapi,
}


def require_key(provider: str) -> str:
    key = get_key(PROVIDERS[provider].env)
    if not key:
        raise SearchError(f"Add your {PROVIDERS[provider].name} API key in the sidebar.")
    return key


def search(provider: str, query: str, n: int = 5, news: bool = False, days: int | None = None,
           key: str | None = None) -> list[Result]:
    results = ADAPTERS[provider](key or require_key(provider), query, n, news, days)
    return [r for r in results if r.url.startswith(("http://", "https://"))]


def as_context(results: list[Result]) -> str:
    return "\n\n".join(
        f"[{i}] {r.title}\nURL: {r.url}\n{('Date: ' + r.date + chr(10)) if r.date else ''}{r.snippet[:1500]}"
        for i, r in enumerate(results, 1)
    )
