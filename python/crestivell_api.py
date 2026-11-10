"""Small standard-library client shared by the Crestivell examples (Python 3.10+)."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Do not forward API credentials to a redirect target.


class CrestivellAPI:
    def __init__(self, key_variable="CRESTIVELL_API_KEY"):
        self.url = (os.environ.get("CRESTIVELL_URL") or "http://127.0.0.1:8787").rstrip("/")
        parsed = urlsplit(self.url)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/")):
            raise ValueError("CRESTIVELL_URL must be a server base URL without credentials or a path")
        if os.environ.get("CRESTIVELL_TLS_FINGERPRINT"):
            raise ValueError("CRESTIVELL_TLS_FINGERPRINT is not supported by REST examples; use CrestivellCli for TLS pinning")
        if (parsed.scheme == "http" and parsed.hostname not in ("127.0.0.1", "localhost", "::1")
                and os.environ.get("CRESTIVELL_ALLOW_REMOTE_HTTP") != "1"):
            raise ValueError("Remote connections require HTTPS unless CRESTIVELL_ALLOW_REMOTE_HTTP=1")
        self.key = os.environ.get(key_variable, "")
        if not self.key or any(c in self.key for c in "\r\n"):
            raise ValueError(f"Set {key_variable} to an enabled API key")
        self.opener = build_opener(NoRedirects())

    def request(self, path, method="GET", *, payload=None, raw=None, query=None):
        if not path.startswith("/") or path.startswith("//"):
            raise ValueError("Use a server-relative API path")
        if payload is not None and raw is not None:
            raise ValueError("Supply JSON or raw bytes, not both")
        body = json.dumps(payload).encode("utf-8") if payload is not None else raw
        headers = {"Authorization": "Bearer " + self.key, "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json" if payload is not None else "application/octet-stream"
        url = self.url + path + ("?" + urlencode(query) if query else "")
        try:
            with self.opener.open(Request(url, data=body, headers=headers, method=method), timeout=300) as response:
                data = response.read()
                if "application/json" in response.headers.get("Content-Type", ""):
                    return json.loads(data)
                return data
        except HTTPError as error:
            data = error.read(65536).decode("utf-8", errors="replace")
            try:
                result = json.loads(data)
                detail = str(result.get("error", "Request rejected"))
                code = str(result.get("code", "http_error"))
            except (ValueError, AttributeError):
                detail, code = error.reason, "http_error"
            raise RuntimeError(f"HTTP {error.code} ({code}): {detail}".replace(self.key, "[redacted]")) from None
        except URLError:
            raise RuntimeError("Cannot reach the server; check its URL, TLS trust and connectivity") from None
