import ipaddress
import socket
from io import BytesIO
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
import trafilatura
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError

MAX_BYTES = 5_000_000
MAX_REDIRECTS = 5
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; langchain-examples/1.0)"}


class FetchError(Exception):
    pass


def _pin(url: str) -> tuple[str, dict, dict]:
    """Validate a URL and return a request pinned to one vetted public IP.

    Connecting to the IP we checked, rather than letting httpx resolve the
    name again, closes the DNS-rebinding gap between the check and the request.
    TLS still verifies the certificate against the original hostname via SNI.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise FetchError("Only public http(s) URLs are supported.")
    if parsed.username or parsed.password:
        raise FetchError("URLs with embedded credentials are not supported.")
    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        host = parsed.hostname.encode("idna").decode("ascii")
    except (ValueError, UnicodeError):
        raise FetchError("That URL is not valid.") from None
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        raise FetchError(f"Could not resolve {host}.") from None
    addresses = [info[4][0] for info in infos]
    if not addresses or not all(ipaddress.ip_address(a.split("%")[0]).is_global for a in addresses):
        raise FetchError("That address is not publicly reachable.")
    ip = addresses[0]
    pinned = urlunparse(parsed._replace(netloc=f"[{ip}]:{port}" if ":" in ip else f"{ip}:{port}"))
    default_port = port == (443 if parsed.scheme == "https" else 80)
    headers = {"Host": host if default_port else f"{host}:{port}"}
    extensions = {"sni_hostname": host} if parsed.scheme == "https" else {}
    return pinned, headers, extensions


def _download(url: str) -> tuple[bytes, str, str]:
    try:
        return _fetch(url)
    except httpx.HTTPError as error:
        message = "The site's certificate could not be verified." if "CERTIFICATE" in str(error) else "Could not reach that page."
        raise FetchError(message) from None


def _fetch(url: str) -> tuple[bytes, str, str]:
    with httpx.Client(timeout=20.0, follow_redirects=False, headers=HEADERS, trust_env=False) as client:
        for _ in range(MAX_REDIRECTS + 1):
            pinned, headers, extensions = _pin(url)
            with client.stream("GET", pinned, headers=headers, extensions=extensions) as response:
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
