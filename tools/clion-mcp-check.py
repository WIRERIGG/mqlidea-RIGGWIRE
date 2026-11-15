#!/usr/bin/env python3
"""Live check: ask the running CLion (its built-in MCP server) for every problem it reports on the
MQL files of a project, using whatever mqlidea version is installed. Run it after each install.

  tools/clion-mcp-check.py PROJECT_DIR [SUBDIR] [--expect N] [--port 64362]

Prints one line per problem and the installed plugin version; with --expect, exits 1 unless exactly
N problems come back. get_file_problems is called with errorsOnly=false: its default returns
errors only, and an empty list then looks like a clean project."""
import argparse, glob, json, os, queue, socket, sys, threading, zipfile


class Mcp:
    def __init__(self, port):
        self.port = port
        s = socket.create_connection(("127.0.0.1", port))
        s.sendall(f"GET /sse HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nAccept: text/event-stream\r\n\r\n".encode())
        self.f = s.makefile("rb")
        while self.f.readline() not in (b"\r\n", b""):
            pass
        self.events = queue.Queue()
        threading.Thread(target=self._read, daemon=True).start()
        self.endpoint = None
        while self.endpoint is None:
            e = self.events.get(timeout=15)
            if e and e[0] == "endpoint":
                self.endpoint = e[1]
        self.rpc(1, "initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                   "clientInfo": {"name": "mqlidea-check", "version": "1"}})
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
        self.next_id = 2

    def _chunks(self):  # the SSE stream is chunked; a JSON line can span chunks
        while True:
            size = self.f.readline()
            if not size or int(size.strip() or b"0", 16) == 0:
                return
            yield self.f.read(int(size.strip(), 16))
            self.f.readline()

    def _read(self):
        buf, ev, data = b"", None, []
        for chunk in self._chunks():
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                line = line.decode("utf-8", "replace").rstrip("\r")
                if line.startswith("event:"):
                    ev = line[6:].strip()
                elif line.startswith("data:"):
                    data.append(line[5:].lstrip())
                elif line == "":
                    if data:
                        self.events.put((ev, "\n".join(data)))
                    ev, data = None, []
        self.events.put(None)

    def _post(self, msg):
        body = json.dumps(msg).encode()
        c = socket.create_connection(("127.0.0.1", self.port))
        c.sendall(f"POST {self.endpoint} HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\nContent-Type: application/json\r\n"
                  f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode() + body)
        c.recv(4096)
        c.close()

    def rpc(self, i, method, params, timeout=600):
        self._post({"jsonrpc": "2.0", "id": i, "method": method, "params": params})
        while True:
            e = self.events.get(timeout=timeout)
            if e is None:
                sys.exit("CLion closed the MCP stream")
            try:
                m = json.loads(e[1])
            except ValueError:
                continue
            if m.get("id") == i:
                return m

    def call(self, tool, args):
        self.next_id += 1
        return self.rpc(self.next_id, "tools/call", {"name": tool, "arguments": args})


def installed_version():
    for jar in glob.glob(os.path.expanduser("~/Library/Application Support/JetBrains/CLion*/plugins/mqlidea/lib/mqlidea-*.jar")):
        with zipfile.ZipFile(jar) as z:
            xml = z.read("META-INF/plugin.xml").decode()
            return xml.split("<version>")[1].split("</version>")[0] + f" ({jar.split('/JetBrains/')[1].split('/')[0]})"
    return "not found"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("subdir", nargs="?", default="")
    ap.add_argument("--expect", type=int)
    ap.add_argument("--port", type=int, default=64362)
    a = ap.parse_args()
    project = os.path.abspath(a.project)
    files = sorted(glob.glob(os.path.join(project, a.subdir, "**", "*.mq[45h]"), recursive=True))
    mcp = Mcp(a.port)
    total = 0
    for path in files:
        rel = os.path.relpath(path, project)
        r = mcp.call("get_file_problems", {"filePath": rel, "errorsOnly": False, "timeout": 180000, "projectPath": project})
        res = r.get("result", {})
        problems = (res.get("structuredContent") or {}).get("errors")
        if problems is None:
            print(f"{rel}: FAILED {json.dumps(res)[:300]}")
            total += 1
            continue
        for p in problems:
            print(f"{rel}:{p['line']} [{p['severity']}] {p['description']}")
        total += len(problems)
    print(f"mqlidea {installed_version()}: {len(files)} files, {total} problems")
    if a.expect is not None and total != a.expect:
        sys.exit(f"expected {a.expect} problems, got {total}")


if __name__ == "__main__":
    main()
