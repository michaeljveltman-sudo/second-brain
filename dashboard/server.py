#!/usr/bin/env python3
"""
Command Centre Dashboard Server
Regenerates index.html, serves it at http://localhost:5678,
and exposes two API endpoints for writing to local log files.

Usage:
  python3 server.py          # regenerate, serve, open browser
  python3 server.py --port 5679
"""

import json
import os
import sys
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# Full path to claude CLI — LaunchAgent PATH doesn't include ~/.local/bin
_CLAUDE_BIN = "/Users/michaelveltman/.local/bin/claude"

# Build env for claude subprocess:
# - Strip all CLAUDE_* (avoids nested-session detection + expired OAuth token passthrough)
# - Strip ANTHROPIC_* from server env (LaunchAgent won't have these anyway)
# - Then inject saved auth from ~/.dashboard-auth if present (written by save-auth.sh)
_CLAUDE_ENV = {k: v for k, v in os.environ.items()
               if not k.startswith("CLAUDE") and not k.startswith("ANTHROPIC")}
_CLAUDE_ENV["PATH"] = "/Users/michaelveltman/.local/bin:" + _CLAUDE_ENV.get("PATH", "/usr/bin:/bin")

_AUTH_FILE = Path.home() / ".dashboard-auth"
if _AUTH_FILE.exists():
    for _line in _AUTH_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _CLAUDE_ENV[_k.strip()] = _v.strip()

SECOND_BRAIN  = Path("/Users/michaelveltman/My second brain")
DASHBOARD_DIR = SECOND_BRAIN / "dashboard"
DEFAULT_PORT  = 5678


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Only log errors to keep the console clean
        if args and str(args[1]) not in ("200", "204"):
            try:
                print(f"  [{args[1]}] {fmt % args}")
            except Exception:
                print(f"  [{args[1]}] {args}")

    # ── CORS helpers ───────────────────────────────────────────────────────
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    # ── OPTIONS (preflight) ────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── GET — serve static files ───────────────────────────────────────────
    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            file_path = DASHBOARD_DIR / "index.html"
        else:
            file_path = DASHBOARD_DIR / path.lstrip("/")

        if file_path.is_file():
            content = file_path.read_bytes()
            ext_map = {".html": "text/html", ".js": "text/javascript", ".css": "text/css"}
            ct = ext_map.get(file_path.suffix, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", str(len(content)))
            self._cors()
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    # ── POST — API endpoints ───────────────────────────────────────────────
    def do_POST(self):
        length   = int(self.headers.get("Content-Length", 0))
        body     = json.loads(self.rfile.read(length)) if length else {}
        endpoint = urlparse(self.path).path

        # ── /api/save-log — append to team/<repId>/log.md ─────────────────
        if endpoint == "/api/save-log":
            rep_id  = body.get("repId",   "").strip()
            summary = body.get("summary", "").strip()
            if not rep_id or not summary:
                return self.send_json(400, {"error": "Missing repId or summary"})

            log_file = SECOND_BRAIN / "team" / rep_id / "log.md"
            if not log_file.parent.is_dir():
                return self.send_json(400, {"error": f"Rep directory not found: {rep_id}"})

            # Strip the "Internal Log Entry" block and any trailing offer text
            # that the /summary command appends — only the Slack-format summary belongs in the log
            import re as _re
            summary = _re.split(r'\n\*\*Internal Log Entry', summary)[0].strip()
            summary = _re.split(r'\nWant me to log this', summary)[0].strip()

            date_str = datetime.now().strftime("%d %B %Y")
            new_block = f"## {date_str} — 1:1 Summary\n\n{summary}\n"

            # Prepend after the ENTRIES marker so newest is always first
            MARKER = "<!-- ENTRIES BELOW — newest at top -->"
            content = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
            if MARKER in content:
                idx = content.index(MARKER) + len(MARKER)
                content = content[:idx] + f"\n\n---\n{new_block}" + content[idx:]
                log_file.write_text(content, encoding="utf-8")
            else:
                # No marker — just prepend at top of file
                existing = content or ""
                log_file.write_text(f"{new_block}\n---\n\n{existing}", encoding="utf-8")

            # Regenerate dashboard so rep card picks up new log entry
            try:
                subprocess.run(
                    ["python3", str(DASHBOARD_DIR / "generate.py")],
                    check=True, capture_output=True, cwd=str(SECOND_BRAIN)
                )
            except Exception:
                pass
            print(f"  ✅ Saved 1:1 summary → team/{rep_id}/log.md")
            self.send_json(200, {"ok": True, "path": str(log_file)})

        # ── /api/save-ops-log — append to team/ops-log.md ─────────────────
        elif endpoint == "/api/save-ops-log":
            summary = body.get("summary", "").strip()
            label   = body.get("label",   "Huddle").strip()
            if not summary:
                return self.send_json(400, {"error": "Missing summary"})

            log_file = SECOND_BRAIN / "team" / "ops-log.md"
            date_str = datetime.now().strftime("%d %B %Y")
            entry    = f"\n## {date_str} — {label}\n\n{summary}\n"
            mode     = "a" if log_file.exists() else "w"
            with open(log_file, mode, encoding="utf-8") as f:
                if mode == "w":
                    f.write("# Ops Log\n")
                f.write(entry)

            # Regenerate dashboard
            try:
                subprocess.run(
                    ["python3", str(DASHBOARD_DIR / "generate.py")],
                    check=True, capture_output=True, cwd=str(SECOND_BRAIN)
                )
            except Exception:
                pass
            print(f"  ✅ Saved {label} summary → team/ops-log.md")
            self.send_json(200, {"ok": True, "path": str(log_file)})

        # ── /api/summarize — call claude --print with transcript ──────────
        elif endpoint == "/api/summarize":
            rep_id    = body.get("repId",    "").strip()
            rep_name  = body.get("repName",  "").strip()
            transcript = body.get("transcript", "").strip()
            is_huddle  = body.get("isHuddle", False)
            is_adhoc   = body.get("isAdhoc",  False)

            if not transcript:
                return self.send_json(400, {"error": "No transcript provided"})

            # Load the right command instructions
            # adhoc   → summary.md but no rep context (generic transcript summary)
            # huddle  → huddlesummary.md (transcript → Slack-ready team format)
            # rep 1:1 → summary.md with rep context + recent log
            if is_huddle:
                cmd_name = "huddlesummary.md"
            else:
                cmd_name = "summary.md"
            cmd_file = SECOND_BRAIN / ".claude/commands/" / cmd_name
            instructions = cmd_file.read_text(encoding="utf-8") if cmd_file.exists() else ""

            # Load rep context + recent log (only for rep 1:1s)
            context_text = ""
            log_text     = ""
            if rep_id and not is_huddle and not is_adhoc:
                import re as _re
                ctx_file = SECOND_BRAIN / "team" / rep_id / "context.md"
                log_file = SECOND_BRAIN / "team" / rep_id / "log.md"
                if ctx_file.exists():
                    context_text = ctx_file.read_text(encoding="utf-8")
                if log_file.exists():
                    content = log_file.read_text(encoding="utf-8")
                    blocks  = _re.split(r'\n---\n', content)
                    recent  = [b.strip() for b in blocks
                               if _re.search(r'^##\s+\d', b.strip(), _re.MULTILINE)][:3]
                    log_text = "\n---\n".join(recent)

            # Name mismatch check — only for rep 1:1s
            first_name   = rep_name.split()[0].lower() if rep_name and not is_huddle and not is_adhoc else ""
            name_warning = bool(first_name) and (first_name not in transcript.lower())

            # Build the full prompt
            parts = [f"INSTRUCTIONS:\n{instructions}"]
            if context_text:
                parts.append(f"REP CONTEXT:\n{context_text}")
            if log_text:
                parts.append(f"RECENT LOG (last 3 sessions):\n{log_text}")
            parts.append(f"TRANSCRIPT:\n{transcript}")
            parts.append("Produce the summary now following the instructions exactly.")
            full_prompt = "\n\n---\n\n".join(parts)

            try:
                result = subprocess.run(
                    [_CLAUDE_BIN, "--print", "--dangerously-skip-permissions",
                     "--allowedTools", "Read,Glob"],
                    input=full_prompt,
                    capture_output=True, text=True, timeout=180,
                    cwd=str(SECOND_BRAIN),
                    env=_CLAUDE_ENV
                )
                if result.returncode != 0:
                    err = (result.stderr.strip() or result.stdout.strip() or "Claude exited with no output")
                    print(f"  ✗ claude rc={result.returncode} stderr={result.stderr[:300]!r} stdout={result.stdout[:200]!r}")
                    return self.send_json(500, {"error": err[:300]})
                self.send_json(200, {
                    "ok": True,
                    "summary": result.stdout.strip(),
                    "name_warning": name_warning
                })
                label = 'huddle' if is_huddle else ('ad hoc' if is_adhoc else rep_name)
                print(f"  ✅ Summarized {label}"
                      + (" ⚠️ name mismatch" if name_warning else ""))
            except subprocess.TimeoutExpired:
                self.send_json(500, {"error": "Timed out — transcript may be too long"})
            except FileNotFoundError:
                self.send_json(500, {"error": "claude CLI not found in PATH"})

        # ── /api/add-note — quick note/action to a rep's log ────────────────
        elif endpoint == "/api/add-note":
            rep_id = body.get("repId", "").strip()
            note   = body.get("text",  "").strip()
            ntype  = body.get("type",  "note").strip()
            if not rep_id or not note:
                return self.send_json(400, {"error": "Missing repId or text"})
            log_file = SECOND_BRAIN / "team" / rep_id / "log.md"
            if not log_file.parent.is_dir():
                return self.send_json(400, {"error": f"Rep directory not found: {rep_id}"})
            date_str = datetime.now().strftime("%d %B %Y")
            type_labels = {
                "note":     "Manager Note",
                "action":   "Action Item",
                "response": "Rep Response",
                "closed":   "Closed Item",
            }
            type_label = type_labels.get(ntype, "Note")
            # Format: action items appear as "- Rep:" so they show in card; others as "- Manager:"
            if ntype == "action":
                bullet = f"- Rep: {note}"
            elif ntype == "closed":
                bullet = f"- ✅ Closed: {note}"
            else:
                bullet = f"- Manager: {note}"
            new_block = f"## {date_str} — {type_label}\n\n{bullet}\n"
            MARKER = "<!-- ENTRIES BELOW \u2014 newest at top -->"
            content = log_file.read_text(encoding="utf-8") if log_file.exists() else ""
            if MARKER in content:
                idx = content.index(MARKER) + len(MARKER)
                content = content[:idx] + f"\n\n---\n{new_block}" + content[idx:]
            else:
                content = f"{new_block}\n---\n\n{content}"
            log_file.write_text(content, encoding="utf-8")
            try:
                subprocess.run(
                    ["python3", str(DASHBOARD_DIR / "generate.py")],
                    check=True, capture_output=True, cwd=str(SECOND_BRAIN)
                )
            except Exception:
                pass
            print(f"  ✅ Quick note ({type_label}) → team/{rep_id}/log.md")
            self.send_json(200, {"ok": True})

        # ── /api/version — mtime of index.html for auto-refresh polling ───
        elif endpoint == "/api/version":
            html_file = DASHBOARD_DIR / "index.html"
            mtime = int(html_file.stat().st_mtime) if html_file.exists() else 0
            self.send_json(200, {"v": mtime})

        # ── /api/regenerate — rebuild index.html without restarting ────────
        elif endpoint == "/api/regenerate":
            try:
                subprocess.run(
                    ["python3", str(DASHBOARD_DIR / "generate.py")], check=True, capture_output=True
                )
                print("  ⟳  Dashboard regenerated")
                self.send_json(200, {"ok": True})
            except subprocess.CalledProcessError as e:
                self.send_json(500, {"error": e.stderr.decode()})

        else:
            self.send_json(404, {"error": "Unknown endpoint"})


def run(port: int = DEFAULT_PORT):
    # 1. Regenerate dashboard HTML first
    print("⟳  Generating dashboard…")
    subprocess.run(["python3", str(DASHBOARD_DIR / "generate.py")], check=True)
    print("✓  index.html ready\n")

    # 2. Start HTTP server
    server = HTTPServer(("localhost", port), Handler)
    url    = f"http://localhost:{port}"
    print(f"⚡ Dashboard → {url}")
    print(f"   Save-log API  → {url}/api/save-log")
    print(f"   Ops-log API   → {url}/api/save-ops-log")
    print(f"   Ctrl+C to stop\n")

    # 3. Open in browser
    subprocess.Popen(["open", url])

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓  Server stopped.")


if __name__ == "__main__":
    port = DEFAULT_PORT
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    run(port)
