"""HTTP transport shared by the service clients."""

import json
import socket
import urllib.error
import urllib.request


class HttpTransport:
    """Sends JSON requests to a service and returns the decoded body.

    ``get`` returns ``None`` when the service answers 404. A request that
    takes longer than ``timeout`` seconds raises ``TimeoutError``.
    """

    def __init__(self, base_url, headers=None):
        self._base_url = base_url.rstrip("/")
        self._headers = dict(headers or {})

    def get(self, path, timeout):
        return self._send("GET", path, None, {}, timeout)

    def post(self, path, body, headers, timeout):
        return self._send("POST", path, body, headers, timeout)

    def _send(self, method, path, body, headers, timeout):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(self._base_url + path, data=data, method=method)
        for name, value in {**self._headers, **headers}.items():
            request.add_header(name, value)
        request.add_header("Accept", "application/json")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            raise
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise TimeoutError(path) from exc
            raise
        except socket.timeout as exc:
            raise TimeoutError(path) from exc
