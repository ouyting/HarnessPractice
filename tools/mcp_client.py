"""Small synchronous MCP client: stdio and Streamable HTTP, no OAuth token scraping."""
import json
import math
import os
import queue
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

LIMIT = 8 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class MCPClient:
    def __init__(self, config, root):
        self.config, self.root = config, root
        self.timeout = config.get("timeout_seconds", 30)
        if isinstance(self.timeout, bool) or not isinstance(self.timeout, (int, float)) or not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("MCP timeout must be positive and finite.")
        self.counter, self.process, self.session = 0, None, None
        self.version = "2025-06-18"
        self.messages = queue.Queue(maxsize=256)

    def __enter__(self):
        try:
            transport = self.config.get("transport")
            if transport == "stdio":
                command = self.config.get("command")
                if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
                    raise ValueError("Configure MCP stdio command as an argv array.")
                self.process = subprocess.Popen(command, cwd=self.root, stdin=subprocess.PIPE,
                                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                threading.Thread(target=self._reader, daemon=True).start()
            elif transport == "http":
                url = urllib.parse.urlparse(self.config.get("url", ""))
                if url.username or url.password or url.query or url.fragment:
                    raise ValueError("MCP URL must not contain credentials, query or fragment.")
                if url.scheme != "https" and not (url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1", "::1")):
                    raise ValueError("Use HTTPS MCP endpoint (HTTP allowed only on loopback).")
            else:
                raise ValueError("Configure Jira MCP transport: stdio or http. See docs/V2.1-Adapters.md.")
            result = self.call("initialize", {"protocolVersion": self.version, "capabilities": {},
                              "clientInfo": {"name": "harness", "version": "2.1"}})
            self.version = result.get("protocolVersion")
            if self.version not in ("2025-06-18", "2025-03-26", "2024-11-05"):
                raise ValueError("Unsupported negotiated MCP protocol version.")
            self.call("notifications/initialized", notification=True)
            return self
        except BaseException:
            self.close()
            raise

    def _reader(self):
        try:
            while True:
                line = self.process.stdout.readline(LIMIT + 1)
                if not line:
                    self.messages.put(None)
                    return
                if len(line) > LIMIT:
                    self.messages.put(ValueError("MCP message exceeds size limit."))
                    return
                self.messages.put(json.loads(line))
        except (ValueError, OSError) as error:
            self.messages.put(error)

    def call(self, method, params=None, notification=False):
        self.counter += 1
        payload = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notification:
            payload["id"] = self.counter
        deadline = time.monotonic() + self.timeout
        if self.process:
            self.process.stdin.write((json.dumps(payload) + "\n").encode())
            self.process.stdin.flush()
            if notification:
                return None
            while True:
                try:
                    response = self.messages.get(timeout=max(0.001, deadline - time.monotonic()))
                except queue.Empty:
                    raise ValueError("MCP request timed out.") from None
                if response is None or isinstance(response, Exception):
                    raise ValueError("MCP server closed or emitted invalid JSON.")
                if not isinstance(response, dict):
                    raise ValueError("MCP message must be an object.")
                if response.get("id") == payload["id"]:
                    break
                if "method" in response and "id" in response:
                    refusal = {"jsonrpc": "2.0", "id": response["id"], "error": {"code": -32601, "message": "Client requests not supported"}}
                    self.process.stdin.write((json.dumps(refusal) + "\n").encode())
                    self.process.stdin.flush()
                if time.monotonic() >= deadline:
                    raise ValueError("MCP request timed out.")
        else:
            response = self._http(payload, notification)
            if notification:
                return None
        if not isinstance(response, dict) or response.get("id") != payload["id"] or response.get("jsonrpc") != "2.0":
            raise ValueError("Invalid MCP response envelope.")
        if "error" in response:
            raise ValueError("MCP request failed; check tool schema/server logs (remote details omitted).")
        if not isinstance(response.get("result"), dict):
            raise ValueError("MCP result must be an object.")
        return response["result"]

    def _http(self, payload, notification):
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session:
            headers["Mcp-Session-Id"] = self.session
        if payload["method"] != "initialize":
            headers["MCP-Protocol-Version"] = self.version
        token_env = self.config.get("token_env")
        if token_env:
            token = os.environ.get(token_env)
            if not token:
                raise ValueError("Set configured MCP token environment variable, or use an authenticated stdio bridge.")
            headers["Authorization"] = "Bearer " + token
        request = urllib.request.Request(self.config["url"], json.dumps(payload).encode(), headers)
        try:
            with urllib.request.build_opener(NoRedirect).open(request, timeout=self.timeout) as stream:
                self.session = stream.headers.get("Mcp-Session-Id", self.session)
                if notification:
                    return None
                if "text/event-stream" in stream.headers.get("Content-Type", ""):
                    data, count, deadline = [], 0, time.monotonic() + self.timeout
                    while time.monotonic() < deadline:
                        raw = stream.readline(LIMIT + 1)
                        count += len(raw)
                        if count > LIMIT:
                            raise ValueError("MCP response too large.")
                        if not raw:
                            break
                        line = raw.decode("utf-8").rstrip("\r\n")
                        if line.startswith("data:"):
                            data.append(line[5:].lstrip())
                        elif not line and data:
                            value = json.loads("\n".join(data))
                            if value.get("id") == payload.get("id"):
                                return value
                            data = []
                    raise ValueError("MCP SSE ended/timed out without matching response.")
                raw = stream.read(LIMIT + 1)
                if len(raw) > LIMIT:
                    raise ValueError("MCP response too large.")
                return json.loads(raw)
        except urllib.error.HTTPError as error:
            raise ValueError("MCP HTTP status " + str(error.code) + "; authenticate/configure endpoint; redirects are not followed.") from None
        except urllib.error.URLError:
            raise ValueError("MCP endpoint unavailable; check network/server configuration.") from None

    def list_tools(self):
        found, cursor, seen = [], None, set()
        for _ in range(100):
            page = self.call("tools/list", {"cursor": cursor} if cursor else {})
            tools = page.get("tools")
            if not isinstance(tools, list):
                raise ValueError("MCP tools/list must return tools array.")
            found.extend(tools)
            cursor = page.get("nextCursor")
            if not cursor:
                return found
            if cursor in seen:
                raise ValueError("Repeated MCP pagination cursor.")
            seen.add(cursor)
        raise ValueError("MCP pagination limit exceeded.")

    def close(self):
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait()
            self.process.stdin.close()
            self.process.stdout.close()

    def __exit__(self, *args):
        self.close()
