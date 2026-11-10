"""Exercise example environment settings against local fixtures, never a signing server."""
import http.server
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT
requests = []
PE = b"MZ" + bytes(58) + (64).to_bytes(4, "little") + b"PE\0\0" + bytes(128)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, value, content_type="application/json"):
        body = json.dumps(value).encode() if content_type == "application/json" else value
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        requests.append((self.path, self.headers.get("Authorization"), None))
        self.respond({"uploadLimitBytes": 1024, "certificates": []})

    def do_POST(self):
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        if self.path.startswith("/api/v1/sign-file?"):
            requests.append((self.path, self.headers.get("Authorization"), raw))
            self.respond(PE, "application/octet-stream")
        else:
            data = json.loads(raw)
            requests.append((self.path, self.headers.get("Authorization"), data))
            self.respond(dict(ok=True, signature="dGVzdA==", requestId=data["requestId"],
                              certificateLabel=data["certificateLabel"], demonstrationOnly=True))


def main():
    runtimes = {"python": [sys.executable, str(EXAMPLES / "python/sign.py")]}
    for name, executable, script in [("js", "node", "js/sign.mjs"),
                                      ("powershell", "pwsh", "powershell/sign.ps1")]:
        runtime = shutil.which(executable)
        if runtime:
            runtimes[name] = [runtime, *(["-NoProfile", "-File"] if name == "powershell" else []),
                              str(EXAMPLES / script)]
        else:
            print("SKIP", name, "runtime unavailable")
    dotnet = shutil.which("dotnet")
    if dotnet and subprocess.run([dotnet, "script", "--version"], capture_output=True).returncode == 0:
        runtimes["csharpx"] = [dotnet, "script", str(EXAMPLES / "csharpx/sign.csx"), "--"]
    else:
        print("SKIP csharpx: .NET SDK/dotnet-script unavailable")

    servers = [http.server.ThreadingHTTPServer((host, 0), Handler) for host in ["127.0.0.1", "127.0.0.2"]]
    for server in servers:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    # Remove inherited product settings and proxy credentials; fixtures use synthetic values only.
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith("CRESTIVELL_") and not k.upper().endswith("_PROXY")}
    env.update(CRESTIVELL_URL=f"http://127.0.0.1:{servers[0].server_port}",
               CRESTIVELL_API_KEY="fixture-sign", CRESTIVELL_ADMIN_API_KEY="fixture-admin",
               CRESTIVELL_CERT_LABEL="environment-label", CRESTIVELL_CERT_THUMBPRINT="A" * 40,
               CRESTIVELL_FILE_NAME="environment.exe", NO_PROXY="*")

    try:
        with tempfile.TemporaryDirectory(prefix="crestivell-examples-") as folder:
            work = Path(folder)
            source = work / "input.exe"
            source.write_bytes(PE)

            def run(command, arguments, overrides=None, expected=0):
                result = subprocess.run([*command, *map(str, arguments)], cwd=work,
                                        env={**env, **(overrides or {})}, capture_output=True,
                                        text=True, timeout=25)
                assert (result.returncode == 0) == (expected == 0), result
                assert "fixture-sign" not in result.stdout + result.stderr, result
                return result

            for name, command in runtimes.items():
                for explicit in [False, True]:
                    output = work / f"{name}-{explicit}.json"
                    if name == "python":
                        args = ["digest", "--sha256", "0" * 64, "--output", output]
                        if explicit:
                            args += ["--label", "explicit-label", "--thumbprint", "B" * 40,
                                     "--filename", "explicit.exe"]
                    elif name == "powershell":
                        args = ["digest", "-Sha256", "0" * 64, "-Output", output]
                        if explicit:
                            args += ["-Label", "explicit-label", "-Thumbprint", "B" * 40,
                                     "-FileName", "explicit.exe"]
                    else:
                        args = ["digest", "0" * 64, *(["B" * 40, "explicit.exe", "explicit-label"]
                                if explicit else ["-", "-", "-"]), output]
                    run(command, args)
                    path, authorization, data = requests[-1]
                    assert path == "/api/v1/sign" and authorization == "Bearer fixture-sign"
                    assert data["certificateLabel"] == ("explicit-label" if explicit else "environment-label")
                    assert data["certificateThumbprint"] == ("B" if explicit else "A") * 40
                    assert data["fileName"] == ("explicit.exe" if explicit else "environment.exe")
                    assert output.exists()
                    count = len(requests)
                    run(command, args, expected=1)
                    assert len(requests) == count, "Existing output caused a signing request"

                output = work / f"{name}.exe"
                args = (["upload", "--file", source, "--output", output] if name == "python" else
                        ["upload", "-File", source, "-Output", output] if name == "powershell" else
                        ["upload", source, output])
                run(command, args)
                assert parse_qs(urlsplit(requests[-1][0]).query)["label"] == ["environment-label"]
                assert output.read_bytes() == source.read_bytes()

                count = len(requests)
                result = run(command, ["certificates"], {"CRESTIVELL_TLS_FINGERPRINT": "A" * 64}, expected=1)
                assert "not supported" in result.stderr and len(requests) == count
                remote = f"http://127.0.0.2:{servers[1].server_port}"
                for value in ["", "0", "true"]:
                    result = run(command, ["certificates"], {"CRESTIVELL_URL": remote,
                                 "CRESTIVELL_ALLOW_REMOTE_HTTP": value}, expected=1)
                    assert "require HTTPS" in result.stderr and len(requests) == count
                run(command, ["certificates"], {"CRESTIVELL_URL": remote, "CRESTIVELL_ALLOW_REMOTE_HTTP": "1"})
                assert len(requests) == count + 1
                print("PASS", name, "environment defaults, overrides, upload, output preservation, pin guard, HTTP opt-in")

            run([sys.executable, str(EXAMPLES / "python/admin.py")], ["list", "settings"])
            assert requests[-1][1] == "Bearer fixture-admin"
            print("PASS Python separate administration key")

            cli = Path(os.environ.get("CRESTIVELL_CLI") or shutil.which("CrestivellCli.exe") or ROOT / "CrestivellCli.exe")
            if os.name == "nt" and cli.exists():
                wrapper = EXAMPLES / "cmd/sign-digest.cmd"
                command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(wrapper)]
                for explicit in [False, True]:
                    args = ["0" * 64, "explicit.exe"] + (["explicit-label"] if explicit else [])
                    run(command, args, {"CRESTIVELL_CLI": str(cli)})
                    data = requests[-1][2]
                    assert data["certificateLabel"] == ("explicit-label" if explicit else "environment-label")
                    assert data["certificateThumbprint"] == "A" * 40
                wrapper = EXAMPLES / "cmd/sign-file.cmd"
                command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", str(wrapper)]
                for explicit in [False, True]:
                    output = work / f"cmd-{explicit}.exe"
                    args = [source, output] + (["explicit-label"] if explicit else [])
                    run(command, args, {"CRESTIVELL_CLI": str(cli)})
                    query = parse_qs(urlsplit(requests[-1][0]).query)
                    assert query["label"] == ["explicit-label" if explicit else "environment-label"]
                    assert output.read_bytes() == PE
                print("PASS CMD upload/digest label defaults, overrides and inherited thumbprint")
            else:
                print("SKIP CMD: Windows CLI unavailable")
    finally:
        for server in servers:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    main()
