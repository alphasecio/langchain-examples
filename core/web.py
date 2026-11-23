import ipaddress
import socket
from io import BytesIO
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

MAX_BYTES = 5_000_000
MAX_REDIRECTS = 5
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; langchain-examples/1.0)"}


class FetchError(Exception):
    pass


def _check_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("Only public http(s) URLs are supported.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror:
        raise FetchError(f"Could not resolve {parsed.hostname}.") from None
    for info in infos:
        if not ipaddress.ip_address(info[4][0]).is_global:
            raise FetchError("That address is not publicly reachable.")


def _download(url: str) -> tuple[bytes, str, str]:
    with httpx.Client(timeout=20.0, follow_redirects=False, headers=HEADERS) as client:
        for _ in range(MAX_REDIRECTS + 1):
            _check_url(url)
            with client.stream("GET", url) as response:
                if response.is_redirect:
                    url = urljoin(url, response.headers.get("location", ""))
                    continue
                if response.status_code >= 400:
                    raise FetchError(f"The page returned HTTP {response.status_code}.")
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        raise FetchError("The page is larger than 5 MB.")
                return bytes(body), response.headers.get("content-type", ""), url
    raise FetchError("Too many redirects.")


def pdf_text(data: bytes) -> list[str]:
    try:
        return [page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages]
    except FileNotDecryptedError:
        raise FetchError("This PDF is password-protected. Remove the password and try again.") from None
    except PdfReadError:
        raise FetchError("Could not read this PDF.") from None


def fetch_text(url: str) -> tuple[str, str]:
    data, content_type, final_url = _download(url.strip())
    if "pdf" in content_type or final_url.lower().endswith(".pdf"):
        return final_url, "\n\n".join(pdf_text(data))
    html = data.decode("utf-8", errors="replace")
    text = trafilatura.extract(html, url=final_url, include_comments=False, include_tables=True)
    if not text:
        raise FetchError("No readable text found on that page.")
    return final_url, text
