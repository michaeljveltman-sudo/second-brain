#!/usr/bin/env python3
"""
Command Centre Dashboard Generator
Reads progress.md + team logs → writes self-contained index.html
Usage:
  python3 generate.py          # generate only
  python3 generate.py --open   # generate + open in browser
"""

import re
import json
import sys
import subprocess
import shutil
from datetime import datetime, date
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
SECOND_BRAIN   = Path("/Users/michaelveltman/My second brain")
PROGRESS_FILE  = SECOND_BRAIN / "progress.md"
TEAM_DIR       = SECOND_BRAIN / "team"
SCHEDULE_FILE  = SECOND_BRAIN / "schedule.json"
OUTPUT_FILE    = SECOND_BRAIN / "dashboard" / "index.html"

# ── Reps ─────────────────────────────────────────────────────────────────────
REPS = [
    {"id": "emilio",    "name": "Emilio"},
    {"id": "annmarie",  "name": "Annmarie"},
    {"id": "thiago",    "name": "Thiago"},
    {"id": "cormac",    "name": "Cormac"},
    {"id": "eleonora",  "name": "Eleonora"},
    {"id": "mike-lyon", "name": "Mike Lyon"},
]

# ── Commands ──────────────────────────────────────────────────────────────────
COMMANDS = [
    {"group": "🏢 Toptal — Team",     "cmd": "/1on1",       "args": "[name]",       "desc": "Prep a 1:1 before it happens"},
    {"group": "🏢 Toptal — Team",     "cmd": "/summary",    "args": "[name]",       "desc": "Slack-ready 1:1 summary from transcript"},
    {"group": "🏢 Toptal — Team",     "cmd": "/log",        "args": "[name]",       "desc": "Log a coaching session"},
    {"group": "🏢 Toptal — Team",     "cmd": "/teamreview", "args": "",             "desc": "Weekly team review"},
    {"group": "🏢 Toptal — Pipeline", "cmd": "/pipeline",   "args": "",             "desc": "Review & prioritise pipeline"},
    {"group": "🏢 Toptal — Pipeline", "cmd": "/discovery",  "args": "[company]",    "desc": "Discovery call prep briefing"},
    {"group": "🏢 Toptal — Pipeline", "cmd": "/followup",   "args": "[company]",    "desc": "Post-call follow-up email"},
    {"group": "🏢 Toptal — Pipeline", "cmd": "/proposal",   "args": "[company]",    "desc": "Build a client proposal"},
    {"group": "🎮 Side Quest",         "cmd": "/linkedin",   "args": "",             "desc": "Draft a LinkedIn post"},
    {"group": "🎮 Side Quest",         "cmd": "/lesson",     "args": "[topic]",      "desc": "Build teaching content"},
    {"group": "📄 Docs",              "cmd": "/email",      "args": "",             "desc": "Draft an email in your voice"},
    {"group": "📄 Docs",              "cmd": "/brief",      "args": "",             "desc": "Create a project brief"},
    {"group": "⚙️ System",            "cmd": "/progress",   "args": "",             "desc": "View progress bars"},
    {"group": "⚙️ System",            "cmd": "/menu",       "args": "",             "desc": "Show command launcher"},
    {"group": "⚙️ System",            "cmd": "/dashboard",  "args": "",             "desc": "Refresh this dashboard"},
]

UPDATE_FIELDS = [
    {"key": "revenue",    "label": "Revenue (QTD)",         "kv": "TOPTAL_REVENUE"},
    {"key": "week",       "label": "Current Week",           "kv": "TOPTAL_WEEK"},
    {"key": "1on1s",      "label": "1:1s Done This Week",    "kv": "TOPTAL_1ON1S_DONE"},
    {"key": "actions",    "label": "Open Actions",           "kv": "TOPTAL_OPEN_ACTIONS"},
    {"key": "track1",     "label": "Track 1 Progress (%)",   "kv": "SH_TRACK1_PCT"},
    {"key": "track2",     "label": "Track 2 Progress (%)",   "kv": "SH_TRACK2_PCT"},
    {"key": "published",  "label": "Posts Published",        "kv": "SH_POSTS_PUBLISHED"},
    {"key": "drafted",    "label": "Posts Drafted",          "kv": "SH_POSTS_DRAFTED"},
    {"key": "pieces",     "label": "Active Pieces",          "kv": "SH_ACTIVE_PIECES"},
    {"key": "status",     "label": "Side Quest Status",      "kv": "SH_STATUS"},
]

# ── Data extraction ───────────────────────────────────────────────────────────
def extract_progress():
    if not PROGRESS_FILE.exists():
        return {}
    content = PROGRESS_FILE.read_text()
    vals = {}
    for m in re.finditer(r'<!-- ([A-Z_]+): ([^>-]+?) -->', content):
        key, val = m.group(1), m.group(2).strip()
        try:    vals[key] = int(val)
        except ValueError:
            try:    vals[key] = float(val)
            except ValueError:
                vals[key] = val
    return vals

def get_rep_data(rep):
    log_file = TEAM_DIR / rep["id"] / "log.md"
    if not log_file.exists():
        return {"signal": "unknown", "last_session": "—", "signal_text": "No log",
                "signal_reason": "", "last_session_type": "", "rep_actions": [], "entries": []}
    content = log_file.read_text()
    signals = re.findall(r'\*\*Signal\*\*:\s*([^\n]+)', content)
    signal, signal_text, signal_reason = "yellow", "Watch", ""
    if signals:
        s = signals[0]
        signal_text = s.strip()
        signal_reason = re.sub(r'^[🟢🟡🔴🟠⚪]\s*', '', s.strip()).strip()
        if '🟢' in s or 'Strong' in s:
            signal, signal_text = "green", "Strong"
        elif '🔴' in s or 'Risk' in s or 'risk' in s.lower():
            signal, signal_text = "red", "Risk"
        else:
            signal, signal_text = "yellow", "Watch"
    dates = re.findall(r'##\s+(\d+\s+\w+\s+\d{4})\s+[—-]', content)
    last_session = dates[0] if dates else "No sessions"

    # Collect dated entry blocks (last 5 for notes access)
    entries = []
    for block in re.split(r'\n---\n', content):
        b = block.strip()
        if re.search(r'^##\s+\d', b, re.MULTILINE):
            h = re.search(r'^##\s+(.+)', b, re.MULTILINE)
            if h:
                hend = b.find(h.group(0)) + len(h.group(0))
                entries.append({"title": h.group(1).strip(), "body": b[hend:].strip()})
        if len(entries) >= 5:
            break

    first_entry = entries[0] if entries else {}
    first_body  = first_entry.get("body", "")
    first_title = first_entry.get("title", "")

    # Session type from first entry header
    type_match = re.search(r'^##\s+\d+\s+\w+\s+\d{4}\s+[—-]\s*(.+)', "## " + first_title, re.MULTILINE) if first_title else None
    last_session_type = type_match.group(1).strip() if type_match else ""

    # Rep actions: old "- Rep:" format OR new ":one:/:two:/:three:" summary format
    rep_actions = re.findall(r'-\s+Rep:\s*([^\n]+)', first_body)
    if not rep_actions:
        # Parse :one: Action text → outcome (strip → part)
        raw = re.findall(r':(?:one|two|three|four|five):\s*([^\n]+)', first_body)
        rep_actions = [re.split(r'\s*→\s*', a)[0].strip() for a in raw]
    rep_actions = rep_actions[:3]

    # Michael's commitments from newest entry ("- Michael: ..." lines)
    michael_actions = re.findall(r'-\s+Michael:\s*([^\n]+)', first_body)
    michael_actions = michael_actions[:4]

    # Pattern note from newest entry
    pn = re.findall(r'\*\*Pattern note\*\*:\s*([^\n]+)', first_body)
    pattern_note = pn[0].strip() if pn else ""

    return {"signal": signal, "last_session": last_session, "signal_text": signal_text,
            "signal_reason": signal_reason, "last_session_type": last_session_type,
            "rep_actions": rep_actions, "michael_actions": michael_actions,
            "pattern_note": pattern_note, "entries": entries}

# ── Ops log extraction ───────────────────────────────────────────────────────
def load_ops_log(n=10):
    log_file = TEAM_DIR / "ops-log.md"
    if not log_file.exists():
        return []
    content = log_file.read_text(encoding="utf-8")
    entries = []
    for block in re.split(r'\n---\n', content):
        block = block.strip()
        header_m = re.search(r'^##\s+(.+)', block, re.MULTILINE)
        if not header_m:
            continue
        title = header_m.group(1).strip()
        # Body = everything after the header line
        header_end = block.find(header_m.group(0)) + len(header_m.group(0))
        body = block[header_end:].strip()
        # Only include actual log entries (title starts with a date digit)
        if body and re.match(r'^\d', title):
            entries.append({"title": title, "body": body})
    return entries[:n]

def load_ops_highlights():
    """Parse the most recent ops-log entry for ➡️ actions, 🔁 patterns, 🔴 risks, ✅ wins."""
    log_file = TEAM_DIR / "ops-log.md"
    if not log_file.exists():
        return {"actions": [], "patterns": [], "risks": [], "wins": []}
    content = log_file.read_text(encoding="utf-8")
    recent = ""
    for block in re.split(r'\n---\n', content):
        block = block.strip()
        if re.search(r'^##\s+\d', block, re.MULTILINE):
            recent = block
            break
    if not recent:
        return {"actions": [], "patterns": [], "risks": [], "wins": []}
    actions, patterns, risks, wins = [], [], [], []
    in_actions = False
    for line in recent.split('\n'):
        s = line.strip()
        if not s:
            in_actions = False
            continue
        if '\u27a1\ufe0f' in s or s.startswith('\u279c') or ('➡' in s):
            in_actions = True
            continue
        if in_actions and re.match(r'^\d+\.', s):
            actions.append(re.sub(r'^\d+\.\s*', '', s))
            continue
        else:
            in_actions = False
        if '🔁' in s:
            text = re.sub(r'^[🔁\s]+Pattern:\s*', '', s).strip()
            text = re.sub(r'^[🔁\s]+', '', text).strip()
            if text: patterns.append(text)
        if '🔴' in s and not s.startswith('-') and not s.startswith('*'):
            text = re.sub(r'^[🔴\s]+', '', s).strip()
            if text: risks.append(text)
        if '✅' in s and not s.startswith('-') and not s.startswith('*'):
            text = re.sub(r'^[✅\s]+', '', s).strip()
            if text: wins.append(text)
    return {
        "actions":  actions[:8],
        "patterns": patterns[:4],
        "risks":    risks[:4],
        "wins":     wins[:4],
    }

# ── Schedule extraction ───────────────────────────────────────────────────────
def load_schedule():
    if not SCHEDULE_FILE.exists():
        return {"weeklyTasks": {}, "meetingPrep": [], "categories": {}}
    with open(SCHEDULE_FILE) as f:
        return json.load(f)

def get_today_day():
    """Return lowercase day name for today"""
    return date.today().strftime("%A").lower()

# ── Build data object ─────────────────────────────────────────────────────────
def build_data():
    p = extract_progress()
    revenue     = p.get("TOPTAL_REVENUE", 0)
    target      = p.get("TOPTAL_TARGET",  624270)
    revenue_pct = round((revenue / target) * 100, 1) if target > 0 else 0
    team = [{**rep, **get_rep_data(rep)} for rep in REPS]
    # Aggregate manager todos across all reps (Michael: commitments)
    manager_todos = []
    for r in team:
        for action in r.get("michael_actions", []):
            manager_todos.append({"rep": r["name"], "rep_id": r["id"], "action": action,
                                  "date": r.get("last_session", "")})
    # Also pull from ops-log highlights
    ops_hl = load_ops_highlights()
    for action in ops_hl.get("actions", []):
        manager_todos.append({"rep": "Team", "rep_id": "", "action": action, "date": ""})
    schedule = load_schedule()
    today_day = get_today_day()
    # Ordered Mon–Fri for display
    day_order = ["monday", "tuesday", "wednesday", "thursday", "friday"]
    weekly = []
    for day in day_order:
        tasks = schedule.get("weeklyTasks", {}).get(day, [])
        weekly.append({
            "day": day,
            "label": day.capitalize(),
            "is_today": day == today_day,
            "tasks": tasks
        })
    return {
        "progress":    p,
        "revenue_pct": revenue_pct,
        "team":        team,
        "commands":    COMMANDS,
        "fields":      UPDATE_FIELDS,
        "schedule":    weekly,
        "meeting_prep": schedule.get("meetingPrep", []),
        "categories":  schedule.get("categories", {}),
        "generated":   datetime.now().strftime("%d %b %Y %H:%M"),
        "date_label":  datetime.now().strftime("%A, %d %b %Y"),
        "today_day":   today_day,
        "week":        p.get("TOPTAL_WEEK", "?"),
        "q1_pct":      revenue_pct,
        "one_on_ones": f"{p.get('TOPTAL_1ON1S_DONE', 0)}/{p.get('TOPTAL_1ON1S_TOTAL', 6)}",
        "open_actions":p.get("TOPTAL_OPEN_ACTIONS", 0),
        "ops_log":        load_ops_log(),
        "ops_highlights": ops_hl,
        "manager_todos":  manager_todos,
    }

# ── HTML generation ───────────────────────────────────────────────────────────
def generate_html(data):
    data_json = json.dumps(data, ensure_ascii=False, indent=2)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Command Centre — Michael Veltman</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
  --bg:        #0a0e1a;
  --surface:   #111827;
  --surface2:  #1a2233;
  --border:    #1f2937;
  --border2:   #2d3748;
  --green:     #10b981;
  --green-dim: #064e3b;
  --amber:     #f59e0b;
  --amber-dim: #78350f;
  --red:       #ef4444;
  --red-dim:   #7f1d1d;
  --blue:      #3b82f6;
  --text:      #f9fafb;
  --text2:     #9ca3af;
  --text3:     #8a94a0;
  --mono:      'SF Mono', 'Fira Code', 'Consolas', monospace;
}}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  min-height: 100vh;
}}

/* ── Top Bar ── */
#topbar {{
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  background: #050810;
  border-bottom: 1px solid var(--border2);
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0 20px;
  height: 44px;
  font-family: var(--mono);
  font-size: 12px;
}}
.topbar-logo {{
  font-size: 13px;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.08em;
  padding-right: 20px;
  border-right: 1px solid var(--border2);
  margin-right: 16px;
}}
.topbar-stat {{
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 16px;
  border-right: 1px solid var(--border2);
  height: 100%;
  color: var(--text2);
}}
.topbar-stat .label {{ color: var(--text3); font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; }}
.topbar-stat .value {{ color: var(--text); font-weight: 700; font-size: 14px; }}
.topbar-stat .value.green {{ color: var(--green); }}
.topbar-stat .value.amber {{ color: var(--amber); }}
.topbar-stat .value.red   {{ color: var(--red);   }}
.topbar-date {{
  margin-left: auto;
  color: var(--text3);
  font-size: 11px;
}}
.topbar-refresh {{
  margin-left: 16px;
  background: none;
  border: 1px solid var(--border2);
  color: var(--text3);
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-family: var(--mono);
  transition: all 0.15s;
}}
.topbar-refresh:hover {{ border-color: var(--green); color: var(--green); }}

/* ── Layout ── */
#layout {{
  display: grid;
  grid-template-columns: 240px 1fr;
  min-height: 100vh;
  padding-top: 44px;
}}

/* ── Sidebar ── */
#sidebar {{
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 20px 0;
  position: sticky;
  top: 44px;
  height: calc(100vh - 44px);
  overflow-y: auto;
}}
.sidebar-group-label {{
  padding: 16px 16px 6px;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text3);
  font-weight: 600;
}}
.cmd-btn {{
  display: flex;
  align-items: center;
  width: 100%;
  padding: 7px 16px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  gap: 10px;
  transition: background 0.12s;
  border-left: 2px solid transparent;
}}
.cmd-btn:hover {{
  background: var(--surface2);
  border-left-color: var(--green);
}}
.cmd-btn .cmd-name {{
  font-family: var(--mono);
  font-size: 12px;
  color: var(--green);
  flex-shrink: 0;
  min-width: 100px;
}}
.cmd-btn .cmd-name .cmd-args {{
  color: var(--text3);
}}
.cmd-btn .cmd-desc {{
  font-size: 11px;
  color: var(--text3);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.sidebar-divider {{
  height: 1px;
  background: var(--border);
  margin: 10px 16px;
}}

/* ── Main content ── */
#main {{
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}}

/* ── Panel card ── */
.panel {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}}
.panel-header {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--surface2);
  border-left: 3px solid var(--green);
}}
.panel-title {{
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.01em;
  display: flex;
  align-items: center;
  gap: 10px;
}}
.panel-badge {{
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 20px;
  font-family: var(--mono);
  font-weight: 600;
}}
.panel-badge.green {{ background: var(--green-dim); color: var(--green); }}
.panel-badge.amber {{ background: var(--amber-dim); color: var(--amber); }}
.panel-badge.red   {{ background: var(--red-dim);   color: var(--red);   }}
.panel-body {{ padding: 20px; }}

/* ── Progress bars ── */
.metric-row {{
  display: grid;
  grid-template-columns: 140px 1fr auto;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}}
.metric-row:last-child {{ margin-bottom: 0; }}
.metric-label {{
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  text-align: right;
}}
.bar-track {{
  background: #0a1525;
  border-radius: 10px;
  height: 20px;
  overflow: hidden;
  border: 1px solid var(--border2);
}}
.bar-fill {{
  height: 100%;
  border-radius: 10px;
  width: 0%;
  transition: width 1s cubic-bezier(0.34, 1.56, 0.64, 1);
}}
.bar-fill.green {{ background: linear-gradient(90deg, #059669, #10b981, #34d399); box-shadow: 0 0 14px #10b98199; }}
.bar-fill.blue  {{ background: linear-gradient(90deg, #1d4ed8, #3b82f6, #60a5fa); box-shadow: 0 0 14px #3b82f688; }}
.bar-fill.amber {{ background: linear-gradient(90deg, #b45309, #f59e0b, #fbbf24); box-shadow: 0 0 14px #f59e0b88; }}
.bar-value {{
  font-family: var(--mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  white-space: nowrap;
  min-width: 150px;
}}
.actions-count {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text2);
}}
.actions-count .num {{
  font-family: var(--mono);
  font-size: 28px;
  font-weight: 800;
  color: var(--amber);
  line-height: 1;
}}

/* ── Team grid ── */
.team-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}}
.rep-card {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-left: 3px solid var(--border2);
  border-radius: 8px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  cursor: pointer;
}}
.rep-card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,0.55); }}
.rep-card.signal-green {{ border-left-color: var(--green); background: linear-gradient(135deg, #061510 0%, var(--surface2) 50%); }}
.rep-card.signal-amber {{ border-left-color: var(--amber); background: linear-gradient(135deg, #120d00 0%, var(--surface2) 50%); }}
.rep-card.signal-red   {{ border-left-color: var(--red);   background: linear-gradient(135deg, #130505 0%, var(--surface2) 50%); }}
.rep-card-top {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.rep-name {{
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.01em;
}}
.signal-dot {{
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
}}
.signal-dot.green {{ background: var(--green); box-shadow: 0 0 8px #10b98166; }}
.signal-dot.amber {{ background: var(--amber); animation: pulse-amber 2s ease-in-out infinite; box-shadow: 0 0 8px #f59e0b66; }}
.signal-dot.red   {{ background: var(--red);   animation: pulse-red   1.5s ease-in-out infinite; box-shadow: 0 0 8px #ef444466; }}
.signal-dot.unknown {{ background: var(--text3); }}

@keyframes pulse-amber {{
  0%, 100% {{ box-shadow: 0 0 0 0 #f59e0b55, 0 0 8px #f59e0b66; }}
  50%       {{ box-shadow: 0 0 0 7px #f59e0b00, 0 0 8px #f59e0b66; }}
}}
@keyframes pulse-red {{
  0%, 100% {{ box-shadow: 0 0 0 0 #ef444455, 0 0 8px #ef444466; }}
  50%       {{ box-shadow: 0 0 0 7px #ef444400, 0 0 8px #ef444466; }}
}}
.rep-signal-label {{
  font-size: 12px;
  font-family: var(--mono);
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}}
.rep-signal-label.green {{ color: var(--green); }}
.rep-signal-label.amber {{ color: var(--amber); }}
.rep-signal-label.red   {{ color: var(--red);   }}
.rep-signal-label.unknown {{ color: var(--text3); }}
.rep-session {{
  font-size: 12px;
  color: var(--text3);
}}
.rep-chevron {{
  font-size: 9px; color: var(--text3); flex-shrink: 0;
  transition: transform 0.25s ease; line-height: 1; margin-top: 2px;
}}
.rep-card.expanded .rep-chevron {{ transform: rotate(180deg); }}
.rep-expand {{
  max-height: 0; overflow: hidden;
  transition: max-height 0.35s ease, opacity 0.2s ease;
  opacity: 0;
}}
.rep-card.expanded .rep-expand {{ max-height: 500px; opacity: 1; }}
.rep-expand-inner {{
  border-top: 1px solid var(--border);
  padding-top: 10px; margin-top: 4px;
  display: flex; flex-direction: column; gap: 10px;
}}
.rep-expand-label {{
  font-size: 9px; font-family: var(--mono); text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--text3); font-weight: 600; margin-bottom: 4px;
}}
/* Signal reason / flag — most prominent text in the expand */
.rep-flag {{
  border-left: 2px solid var(--border2);
  padding-left: 9px;
}}
.rep-flag.green {{ border-color: var(--green); }}
.rep-flag.yellow {{ border-color: var(--amber); }}
.rep-flag.red {{ border-color: var(--red); }}
.rep-flag-text {{
  font-size: 13px; color: var(--text); line-height: 1.55; font-weight: 400;
}}
/* Actions */
.rep-action-bullet {{
  font-size: 12px; color: var(--text2); padding-left: 14px; position: relative; line-height: 1.5;
}}
.rep-action-bullet::before {{ content: '→'; position: absolute; left: 0; color: var(--text3); }}
/* Footer: date + session type + /1on1 btn */
.rep-expand-footer {{
  display: flex; align-items: center; justify-content: space-between;
  padding-top: 6px; border-top: 1px solid var(--border);
  font-size: 11px; font-family: var(--mono); color: var(--text3);
}}
.rep-1on1-btn {{
  font-size: 11px; font-family: var(--mono); background: none;
  border: 1px solid var(--border2); border-radius: 4px; color: var(--text3);
  padding: 3px 10px; cursor: pointer;
  transition: all 0.12s; flex-shrink: 0;
}}
.rep-1on1-btn:hover {{ border-color: var(--green); color: var(--green); background: var(--green-dim); }}

/* ── Side hustle stats ── */
.sh-stats {{
  display: flex;
  gap: 28px;
  margin-top: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}}
.sh-stat {{ display: flex; flex-direction: column; gap: 3px; }}
.sh-stat .sh-val {{ font-family: var(--mono); font-size: 26px; font-weight: 800; color: var(--text); line-height: 1; }}
.sh-stat .sh-key {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text3); font-weight: 500; margin-top: 3px; }}
.sh-status-badge {{
  margin-left: auto;
  align-self: center;
  font-family: var(--mono);
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 20px;
  background: var(--surface2);
  border: 1px solid var(--border2);
  color: var(--text2);
}}

/* ── Updater ── */
.updater-form {{
  display: flex;
  gap: 10px;
  align-items: flex-end;
  flex-wrap: wrap;
}}
.form-group {{
  display: flex;
  flex-direction: column;
  gap: 5px;
}}
.form-label {{
  font-size: 11px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}
select, input[type="text"] {{
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 5px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 13px;
  padding: 7px 10px;
  outline: none;
  transition: border-color 0.15s;
}}
select {{ min-width: 200px; cursor: pointer; }}
input[type="text"] {{ width: 140px; }}
select:focus, input[type="text"]:focus {{ border-color: var(--green); }}
.gen-btn {{
  background: var(--green-dim);
  border: 1px solid var(--green);
  color: var(--green);
  font-family: var(--mono);
  font-size: 12px;
  padding: 7px 16px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s;
  font-weight: 600;
}}
.gen-btn:hover {{ background: var(--green); color: #000; }}
.cmd-output {{
  margin-top: 14px;
  display: none;
}}
.cmd-output .cmd-string {{
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 5px;
  padding: 10px 14px;
  font-family: var(--mono);
  font-size: 13px;
  color: var(--green);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}}
.copy-cmd-btn {{
  background: none;
  border: 1px solid var(--border2);
  color: var(--text3);
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-family: var(--mono);
  transition: all 0.15s;
  white-space: nowrap;
  flex-shrink: 0;
}}
.copy-cmd-btn:hover {{ border-color: var(--green); color: var(--green); }}

/* ── Toast ── */
#toast {{
  position: fixed;
  bottom: 28px;
  right: 24px;
  background: var(--surface2);
  border: 1px solid var(--green);
  color: var(--green);
  font-family: var(--mono);
  font-size: 14px;
  font-weight: 700;
  padding: 12px 20px;
  border-radius: 10px;
  opacity: 0;
  transform: translateY(14px) scale(0.94);
  transition: all 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: none;
  z-index: 999;
  box-shadow: 0 4px 24px rgba(16,185,129,0.25);
  letter-spacing: 0.01em;
}}
#toast.show {{
  opacity: 1;
  transform: translateY(0) scale(1);
}}

/* ── Footer ── */
#footer {{
  padding: 12px 24px;
  font-size: 11px;
  color: var(--text3);
  font-family: var(--mono);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
}}

/* ── This Week schedule ── */
.week-grid {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
}}
.day-col {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}}
.day-col.today {{
  border-color: var(--green);
  box-shadow: 0 0 0 1px var(--green);
}}
.day-header {{
  padding: 10px 12px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--text3);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.day-col.today .day-header {{
  background: var(--green-dim);
  color: var(--green);
}}
@keyframes pulse-green {{
  0%, 100% {{ box-shadow: 0 0 0 0 #10b98155; }}
  50%       {{ box-shadow: 0 0 0 6px #10b98100; }}
}}
.today-badge {{
  font-size: 10px;
  background: var(--green);
  color: #000;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 800;
  letter-spacing: 0.05em;
  animation: pulse-green 2s ease-in-out infinite;
}}
.day-tasks {{
  padding: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}}
.task-chip {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text);
  cursor: pointer;
  transition: all 0.18s cubic-bezier(0.34, 1.56, 0.64, 1);
  border-left: 3px solid transparent;
  position: relative;
}}
.task-chip:hover {{ transform: translateX(3px); opacity: 0.9; }}
.task-chip.done {{ opacity: 0.32; text-decoration: line-through; filter: grayscale(0.6); }}
@keyframes completionFlash {{
  0%   {{ transform: scale(1); }}
  40%  {{ transform: scale(1.05); background: rgba(16,185,129,0.18); }}
  100% {{ transform: scale(1); }}
}}
.task-chip.just-done {{ animation: completionFlash 0.35s ease-out; }}
.task-chip .task-icon {{ font-size: 13px; flex-shrink: 0; }}
.task-chip .task-name {{ flex: 1; line-height: 1.4; }}
.task-chip .task-check {{
  width: 20px; height: 20px;
  border: 1.5px solid rgba(255,255,255,0.22);
  border-radius: 5px;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px;
  transition: all 0.2s;
}}
.task-chip.done .task-check {{
  background: var(--green);
  border-color: var(--green);
  color: #000;
  font-weight: 800;
}}
.empty-day {{ padding: 12px; font-size: 12px; color: var(--text3); text-align: center; cursor: pointer; }}
.empty-day:hover {{ color: var(--green); }}

/* ── Drag & drop ── */
.task-chip[draggable="true"] {{ cursor: grab; }}
.task-chip[draggable="true"]:active {{ cursor: grabbing; }}
.task-chip.dragging {{ opacity: 0.25; transform: scale(0.97); }}
.task-chip.drag-over {{ box-shadow: 0 -3px 0 0 var(--green); }}

/* ── Delete btn (custom tasks) ── */
.task-delete-btn {{
  display: none;
  background: none;
  border: none;
  color: var(--text3);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0 2px;
  flex-shrink: 0;
  border-radius: 3px;
  transition: color 0.12s;
}}
.task-chip:hover .task-delete-btn {{ display: inline; }}
.task-delete-btn:hover {{ color: var(--red) !important; }}
.task-move-btn {{
  display: none;
  background: none;
  border: none;
  color: var(--text3);
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
  padding: 0 2px;
  flex-shrink: 0;
  border-radius: 3px;
}}
.task-chip:hover .task-move-btn {{ display: inline; }}

/* ── Add task button ── */
.add-task-btn {{
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  background: none;
  border: 1px dashed var(--border2);
  border-radius: 6px;
  color: var(--text3);
  font-size: 12px;
  font-family: var(--mono);
  padding: 7px;
  cursor: pointer;
  margin-top: 4px;
  transition: all 0.15s;
  letter-spacing: 0.03em;
}}
.add-task-btn:hover {{ border-color: var(--green); color: var(--green); background: var(--green-dim); }}

/* ── Inline add input ── */
.add-task-input {{
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--green);
  border-radius: 6px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 12px;
  padding: 8px 10px;
  outline: none;
  margin: 4px 0;
  box-shadow: 0 0 8px #10b98133;
}}
.add-task-input::placeholder {{ color: var(--text3); }}

/* ── Meeting Prep tracker ── */
.prep-list {{ display: flex; flex-direction: column; gap: 10px; }}
.prep-card {{
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 16px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 8px;
  align-items: start;
}}
.prep-name {{ font-size: 13px; font-weight: 600; }}
.prep-meta {{ font-size: 11px; color: var(--text3); margin-top: 2px; }}
.prep-slides {{ margin-top: 8px; display: flex; flex-direction: column; gap: 3px; }}
.prep-slide-row {{ font-size: 11px; color: var(--text2); display: flex; gap: 6px; align-items: flex-start; }}
.prep-slide-num {{ color: var(--text3); flex-shrink: 0; font-family: var(--mono); }}
.prep-actions {{ display: flex; flex-direction: column; gap: 5px; align-items: flex-end; }}
.prep-status {{
  font-size: 10px; font-family: var(--mono); font-weight: 700;
  padding: 3px 10px; border-radius: 20px;
}}
.prep-status.pending  {{ background: var(--amber-dim); color: var(--amber); }}
.prep-status.done     {{ background: var(--green-dim); color: var(--green); }}
.prep-status.skipped  {{ background: var(--border);    color: var(--text3); }}
.prep-open-btn {{
  font-size: 10px; font-family: var(--mono);
  background: none; border: 1px solid var(--border2);
  color: var(--text3); padding: 3px 10px; border-radius: 4px;
  cursor: pointer; transition: all 0.15s; white-space: nowrap;
}}
.prep-open-btn:hover {{ border-color: var(--blue); color: var(--blue); }}
.prep-auto-chips {{ display: flex; gap: 4px; flex-wrap: wrap; margin-top: 6px; }}
.auto-chip {{
  font-size: 10px; padding: 2px 7px; border-radius: 10px;
  background: var(--green-dim); color: var(--green);
  font-family: var(--mono);
}}

/* ── Transcript Inbox ── */
.rep-tabs {{
  display: flex;
  border-bottom: 1px solid var(--border);
  overflow-x: auto;
  background: var(--surface2);
}}
.rep-tab-btn {{
  padding: 9px 18px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text2);
  font-size: 12px;
  font-family: var(--mono);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.12s;
  letter-spacing: 0.03em;
}}
.rep-tab-btn:hover {{ color: var(--text); }}
.rep-tab-btn.active {{ color: var(--green); border-bottom-color: var(--green); background: var(--green-dim); }}
.transcript-content {{
  display: none;
  grid-template-columns: 1fr 1fr;
  border-bottom: 1px solid var(--border);
}}
.transcript-col {{
  padding: 16px;
}}
.transcript-col:first-child {{
  border-right: 1px solid var(--border);
}}
.transcript-col-label {{
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text3);
  margin-bottom: 8px;
  font-family: var(--mono);
}}
.transcript-textarea {{
  width: 100%;
  height: 200px;
  background: var(--surface2);
  border: 1px solid var(--border2);
  border-radius: 5px;
  color: var(--text);
  font-family: var(--mono);
  font-size: 11px;
  padding: 10px 12px;
  resize: vertical;
  outline: none;
  line-height: 1.5;
}}
.transcript-textarea:focus {{ border-color: var(--green); }}
.transcript-textarea::placeholder {{ color: var(--text3); }}
.transcript-output-actions {{
  display: flex;
  gap: 8px;
  margin-top: 8px;
}}
.transcript-action-bar {{
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 10px 16px;
  background: var(--surface2);
}}
.t-btn {{
  font-size: 11px;
  font-family: var(--mono);
  padding: 5px 14px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid var(--border2);
  background: none;
  color: var(--text2);
  transition: all 0.12s;
  white-space: nowrap;
}}
.t-btn:hover {{ border-color: var(--green); color: var(--green); }}
.t-btn.primary {{ background: var(--green-dim); border-color: var(--green); color: var(--green); font-weight: 600; }}
.t-btn.primary:hover {{ background: var(--green); color: #000; }}
.t-btn.slack {{ background: #1a2540; border-color: #4285f4; color: #4285f4; }}
.t-btn.slack:hover {{ background: #4285f4; color: #fff; }}
.t-btn.danger {{ border-color: transparent; color: var(--text3); }}
.t-btn.save {{ background: #0d2236; border-color: #3b82f6; color: #60a5fa; }}
.t-btn.save:hover {{ background: #3b82f6; color: #fff; }}
.rep-tab-btn.huddle-tab.active {{ color: var(--amber); border-bottom-color: var(--amber); background: rgba(245,158,11,0.08); }}
.rep-tab-btn.adhoc-tab.active {{ color: #a78bfa; border-bottom-color: #a78bfa; background: rgba(167,139,250,0.08); }}
.voice-btn-inline {{
  background: var(--surface2); border: 1px solid var(--border2);
  border-radius: 4px; padding: 2px 8px; flex-shrink: 0;
  cursor: pointer; font-size: 11px; color: var(--text2);
  transition: all 0.15s; line-height: 1.7; font-family: var(--mono);
  white-space: nowrap;
}}
.voice-btn-inline:hover {{ border-color: var(--green); color: var(--green); background: var(--green-dim); }}
.voice-btn-inline.recording {{
  border-color: var(--red) !important; color: var(--red) !important;
  background: rgba(239,68,68,0.12); animation: pulse-record 1s infinite;
}}
@keyframes pulse-record {{
  0%, 100% {{ box-shadow: 0 0 0 0 rgba(239,68,68,0.4); }}
  50%       {{ box-shadow: 0 0 0 5px rgba(239,68,68,0); }}
}}
.t-btn.danger:hover {{ border-color: var(--red); color: var(--red); }}
.t-spacer {{ flex: 1; }}
.tx-char-count {{ font-size: 10px; color: var(--text3); font-family: var(--mono); }}
.tx-name-warning {{
  display: none;
  background: rgba(239,68,68,0.1);
  border: 1px solid var(--red);
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--red);
  margin-bottom: 8px;
  line-height: 1.4;
}}
.ops-log-viewer {{
  margin-top: 16px; border: 1px solid var(--border);
  border-radius: 6px; overflow: hidden;
}}
.ops-log-viewer-header {{
  padding: 8px 14px; background: var(--surface2);
  border-bottom: 1px solid var(--border);
  font-size: 11px; color: var(--text3);
  font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.05em;
}}
.ops-log-entry {{ border-bottom: 1px solid var(--border); }}
.ops-log-entry:last-child {{ border-bottom: none; }}
.ops-log-entry-title {{
  padding: 9px 14px; cursor: pointer;
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; font-family: var(--mono); color: var(--text2);
  background: var(--surface); transition: background 0.15s; user-select: none;
}}
.ops-log-entry-title:hover {{ background: var(--surface2); color: var(--text); }}
.ops-log-entry-chevron {{ font-size: 9px; color: var(--text3); transition: transform 0.2s; flex-shrink: 0; }}
.ops-log-entry.open .ops-log-entry-chevron {{ transform: rotate(90deg); }}
.ops-log-entry-body {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }}
.ops-log-entry.open .ops-log-entry-body {{ max-height: 800px; }}
.ops-log-entry-body-inner {{
  padding: 10px 16px; font-size: 12px; color: var(--text2);
  line-height: 1.65; white-space: pre-wrap; font-family: var(--mono);
  border-top: 1px solid var(--border); background: var(--bg);
}}
/* ── Status Board ───────────────────────────────────────────────────── */
.status-cards {{
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px;
}}
.status-card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 14px 16px;
}}
.status-card-label {{
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--text3); font-family: var(--mono); margin-bottom: 6px;
}}
.status-card-value {{
  font-size: 24px; font-weight: 700; color: var(--text); line-height: 1.1; margin-bottom: 4px;
}}
.status-card-value.green {{ color: var(--green); }}
.status-card-value.amber {{ color: var(--amber); }}
.status-card-value.red   {{ color: var(--red); }}
.status-card-sub {{ font-size: 11px; color: var(--text3); font-family: var(--mono); }}
.sb-bar {{ height: 3px; background: var(--border); border-radius: 2px; margin: 6px 0 4px; overflow: hidden; }}
.sb-bar-fill {{ height: 100%; border-radius: 2px; transition: width 0.6s ease; }}
.sb-bar-fill.green {{ background: var(--green); }}
.sb-bar-fill.blue  {{ background: #3b82f6; }}
.sb-bar-fill.amber {{ background: var(--amber); }}
.health-pills {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }}
.health-pill {{
  padding: 2px 9px; border-radius: 10px; font-size: 12px; font-weight: 600;
}}
.health-pill.green {{ background: var(--green-dim); color: var(--green); }}
.health-pill.amber {{ background: rgba(245,158,11,0.12); color: var(--amber); }}
.health-pill.red   {{ background: rgba(239,68,68,0.12); color: var(--red); }}
/* ── Team Status Table ──────────────────────────────────────────────── */
.team-status-table {{
  width: 100%; border-collapse: collapse; margin-top: 16px;
}}
.team-status-table th {{
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--text3); font-family: var(--mono); font-weight: 500;
  padding: 7px 12px; border-bottom: 1px solid var(--border);
  background: var(--surface2); text-align: left;
}}
.team-status-table td {{
  padding: 10px 12px; border-bottom: 1px solid var(--border);
  vertical-align: middle;
}}
.team-status-table tr:last-child td {{ border-bottom: none; }}
.tst-name {{ font-size: 13px; font-weight: 600; color: var(--text); white-space: nowrap; }}
.tst-signal {{ display: flex; align-items: center; gap: 6px; }}
.tst-sig-dot {{
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}}
.tst-sig-dot.green {{ background: var(--green); box-shadow: 0 0 5px #10b98166; }}
.tst-sig-dot.yellow {{ background: var(--amber); box-shadow: 0 0 5px #f59e0b66; }}
.tst-sig-dot.red {{ background: var(--red); box-shadow: 0 0 5px #ef444466; }}
.tst-sig-dot.unknown {{ background: var(--text3); }}
.tst-sig-text {{ font-size: 12px; color: var(--text2); }}
.tst-session {{ font-size: 11px; color: var(--text3); font-family: var(--mono); line-height: 1.5; }}
.tst-actions {{ font-size: 12px; color: var(--text2); line-height: 1.6; max-width: 220px; }}
.tst-action-item {{ position: relative; padding-left: 14px; }}
.tst-action-item::before {{ content: '→'; position: absolute; left: 0; color: var(--text3); }}
.quick-add-row {{ display: flex; gap: 5px; align-items: center; min-width: 260px; }}
.qa-select {{
  background: var(--surface2); border: 1px solid var(--border2);
  border-radius: 4px; color: var(--text2); font-size: 11px;
  padding: 4px 6px; font-family: var(--mono); flex-shrink: 0; cursor: pointer;
}}
.qa-input {{
  flex: 1; background: var(--surface2); border: 1px solid var(--border2);
  border-radius: 4px; color: var(--text); font-size: 12px;
  padding: 4px 8px; font-family: var(--mono); min-width: 0;
}}
.qa-input:focus {{ outline: none; border-color: var(--green); }}
.qa-btn {{
  background: var(--surface2); border: 1px solid var(--border2); border-radius: 4px;
  color: var(--text2); font-size: 11px; padding: 4px 10px; cursor: pointer;
  font-family: var(--mono); flex-shrink: 0; transition: all 0.15s;
}}
.qa-btn:hover {{ border-color: var(--green); color: var(--green); background: var(--green-dim); }}
.qa-feedback {{ font-size: 11px; color: var(--green); font-family: var(--mono); margin-top: 4px; display: none; }}
.emea-section {{
  margin-top: 14px;
  display: grid;
  grid-template-columns: 190px 1fr 1fr;
  border: 1px solid var(--border2);
  border-radius: 6px;
  overflow: hidden;
  background: var(--surface);
}}
.emea-col {{
  padding: 14px 16px;
  border-right: 1px solid var(--border);
}}
.emea-col:last-child {{ border-right: none; }}
.emea-col-label {{
  font-size: 10px; text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--text3); font-family: var(--mono); font-weight: 500;
  margin-bottom: 10px; display: flex; align-items: center; gap: 6px;
}}
.emea-stat-row {{
  font-size: 12px; color: var(--text2); line-height: 1.7;
  display: flex; align-items: baseline; gap: 6px;
}}
.emea-stat-label {{ color: var(--text3); font-family: var(--mono); font-size: 11px; }}
.emea-stat-value {{ color: var(--text); font-weight: 600; }}
.ops-item {{
  font-size: 12px; color: var(--text2); padding: 3px 0 3px 18px;
  position: relative; line-height: 1.5;
}}
.ops-item::before {{
  position: absolute; left: 0; font-size: 12px;
}}
.ops-item.action::before  {{ content: '→'; color: var(--amber); }}
.ops-item.pattern::before {{ content: '🔁'; font-size: 10px; top: 4px; }}
.ops-item.risk::before    {{ content: '🔴'; font-size: 10px; top: 4px; }}
.ops-item.win::before     {{ content: '✅'; font-size: 10px; top: 4px; }}
.ops-empty {{ font-size: 11px; color: var(--text3); font-style: italic; }}
/* ── Inline notes panel ─────────────────────────────────────────────── */
.notes-toggle-btn {{
  background: none; border: 1px solid var(--border2); border-radius: 4px;
  color: var(--text3); font-size: 11px; padding: 3px 8px; cursor: pointer;
  font-family: var(--mono); transition: all 0.15s; white-space: nowrap;
}}
.notes-toggle-btn:hover {{ border-color: var(--green); color: var(--green); background: var(--green-dim); }}
.notes-toggle-btn.open {{ border-color: var(--green); color: var(--green); background: var(--green-dim); }}
.notes-panel-row td {{
  padding: 0 !important;
  border-bottom: 1px solid var(--border2);
}}
.notes-panel {{
  overflow: hidden; max-height: 0; transition: max-height 0.3s ease;
}}
.notes-panel.open {{ max-height: 1200px; }}
.notes-panel-inner {{
  padding: 14px 16px; background: var(--bg);
  border-top: 1px solid var(--border);
}}
.notes-entry {{
  margin-bottom: 14px; padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}}
.notes-entry:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
.notes-entry-title {{
  font-size: 11px; font-family: var(--mono); color: var(--text3);
  text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;
}}
.notes-entry-body {{
  font-size: 12px; color: var(--text2); line-height: 1.7;
  white-space: pre-wrap; font-family: var(--mono);
  max-height: 400px; overflow-y: auto;
}}
</style>
</head>
<body>

<script>
const DATA = {data_json};
</script>

<!-- Top Bar -->
<div id="topbar">
  <div class="topbar-logo">⚡ CMD CENTRE</div>
  <div class="topbar-stat">
    <span class="label">Week</span>
    <span class="value" id="tb-week"></span>
  </div>
  <div class="topbar-stat">
    <span class="label">Q1</span>
    <span class="value green" id="tb-q1"></span>
  </div>
  <div class="topbar-stat">
    <span class="label">1:1s</span>
    <span class="value" id="tb-1on1"></span>
  </div>
  <div class="topbar-stat">
    <span class="label">Open</span>
    <span class="value amber" id="tb-actions"></span>
  </div>
  <div class="topbar-stat">
    <span class="label">Score</span>
    <span class="value green" id="tb-score">0 pts</span>
  </div>
  <div class="topbar-date" id="tb-date"></div>
  <button class="topbar-refresh" onclick="copyToClipboard('/dashboard', 'Refresh command copied')">⟳ /dashboard</button>
</div>

<div id="layout">

  <!-- Sidebar -->
  <div id="sidebar" id="sidebar-scroll"></div>

  <!-- Main -->
  <div id="main">

    <!-- Status Board Panel -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📋 Status Board</div>
        <div style="font-size:11px;color:var(--text3);font-family:var(--mono)" id="sb-updated"></div>
      </div>
      <div class="panel-body">
        <div class="status-cards" id="status-cards"></div>
        <div id="activity-bar" style="display:none"></div>
        <table class="team-status-table" id="team-status-table"></table>
        <div class="emea-section" id="emea-section"></div>
      </div>
    </div>

    <!-- Toptal Panel -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🏢 Toptal — Q1 2026</div>
        <div class="panel-badge green" id="toptal-badge"></div>
      </div>
      <div class="panel-body">
        <div class="metric-row">
          <div class="metric-label">Revenue</div>
          <div class="bar-track"><div class="bar-fill green" id="bar-revenue"></div></div>
          <div class="bar-value" id="val-revenue"></div>
        </div>
        <div class="metric-row">
          <div class="metric-label">1:1s this week</div>
          <div class="bar-track"><div class="bar-fill blue" id="bar-1on1"></div></div>
          <div class="bar-value" id="val-1on1"></div>
        </div>
        <div class="actions-count">
          <span class="num" id="val-actions">0</span>
          <span>open action items</span>
        </div>
      </div>
    </div>

    <!-- Team Panel -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">👥 Team Signals</div>
      </div>
      <div class="panel-body">
        <div class="team-grid" id="team-grid"></div>
      </div>
    </div>

    <!-- This Week -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📅 This Week</div>
        <div style="font-size:11px;color:var(--text3);font-family:var(--mono)" id="week-today-label"></div>
      </div>
      <div class="panel-body">
        <div class="week-grid" id="week-grid"></div>
      </div>
    </div>

    <!-- Meeting Prep -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📊 Meeting Prep</div>
        <div style="font-size:11px;color:var(--text3)">Due Monday 09:00 — click to open slides</div>
      </div>
      <div class="panel-body">
        <div class="prep-list" id="prep-list"></div>
      </div>
    </div>

    <!-- Transcript Inbox -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">📝 1:1 Transcript Inbox</div>
        <div style="font-size:11px;color:var(--text3)">Paste transcript → copy /summary command or draft Slack message</div>
      </div>
      <div class="rep-tabs" id="rep-tabs"></div>
      <div id="transcript-panels"></div>
    </div>

    <!-- Metric Updater -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">⚙️ Update a Metric</div>
      </div>
      <div class="panel-body">
        <div class="updater-form">
          <div class="form-group">
            <label class="form-label">Field</label>
            <select id="update-field"></select>
          </div>
          <div class="form-group">
            <label class="form-label">New Value</label>
            <input type="text" id="update-value" placeholder="e.g. 387000">
          </div>
          <button class="gen-btn" onclick="generateUpdateCmd()">Generate Command</button>
        </div>
        <div class="cmd-output" id="cmd-output">
          <div class="cmd-string">
            <span id="cmd-text"></span>
            <button class="copy-cmd-btn" id="copy-cmd-btn" onclick="copyCmdOutput()">Copy</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Side Quest Panel -->
    <div class="panel">
      <div class="panel-header">
        <div class="panel-title">🎮 Side Quest</div>
        <div class="panel-badge amber" id="sh-badge"></div>
      </div>
      <div class="panel-body">
        <div class="metric-row">
          <div class="metric-label">Track 1 · AI for Sales</div>
          <div class="bar-track"><div class="bar-fill green" id="bar-t1"></div></div>
          <div class="bar-value" id="val-t1"></div>
        </div>
        <div class="metric-row">
          <div class="metric-label">Track 2 · Sales for AI</div>
          <div class="bar-track"><div class="bar-fill amber" id="bar-t2"></div></div>
          <div class="bar-value" id="val-t2"></div>
        </div>
        <div class="sh-stats">
          <div class="sh-stat">
            <span class="sh-val" id="sh-published">0</span>
            <span class="sh-key">Published</span>
          </div>
          <div class="sh-stat">
            <span class="sh-val" id="sh-drafted">0</span>
            <span class="sh-key">Drafted</span>
          </div>
          <div class="sh-stat">
            <span class="sh-val" id="sh-active">0</span>
            <span class="sh-key">Active</span>
          </div>
          <div class="sh-status-badge" id="sh-status">building</div>
        </div>
      </div>
    </div>

    <div id="footer">
      <span>Last generated: <span id="footer-gen"></span></span>
      <span>progress.md → dashboard/index.html</span>
    </div>

  </div><!-- /main -->
</div><!-- /layout -->

<div id="toast">Copied!</div>

<script>
// ── Utilities ─────────────────────────────────────────────────────────────
function fmt(n) {{
  return Number(n).toLocaleString('en-US');
}}

function copyToClipboard(text, msg) {{
  if (navigator.clipboard && navigator.clipboard.writeText) {{
    navigator.clipboard.writeText(text)
      .then(() => showToast(msg || 'Copied!'))
      .catch(() => fallbackCopy(text, msg));
  }} else {{
    fallbackCopy(text, msg);
  }}
}}

function fallbackCopy(text, msg) {{
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0;pointer-events:none';
  document.body.appendChild(ta);
  ta.focus(); ta.select();
  try {{
    document.execCommand('copy');
    showToast(msg || 'Copied!');
  }} catch(e) {{
    showToast('⚠️ Copy failed — select and copy manually');
  }}
  document.body.removeChild(ta);
}}

function showToast(msg, duration) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), duration || 1400);
}}

function setBar(id, pct) {{
  setTimeout(() => {{
    document.getElementById(id).style.width = Math.min(100, pct) + '%';
  }}, 80);
}}

// ── Status Board ─────────────────────────────────────────────────────────
(function() {{
  const p        = DATA.progress || {{}};
  const revenue  = p.TOPTAL_REVENUE    || 0;
  const target   = p.TOPTAL_TARGET     || 624270;
  const oneDone  = p.TOPTAL_1ON1S_DONE || 0;
  const oneTotal = p.TOPTAL_1ON1S_TOTAL|| 6;
  const actions  = p.TOPTAL_OPEN_ACTIONS || 0;
  const t1       = p.SH_TRACK1_PCT     || 0;
  const t2       = p.SH_TRACK2_PCT     || 0;
  const shStatus = p.SH_STATUS         || 'building';
  const revPct   = Math.min(100, Math.round(revenue / target * 100));
  const onePct   = Math.min(100, Math.round(oneDone / oneTotal * 100));
  const team     = DATA.team || [];
  const greens   = team.filter(r => r.signal === 'green').length;
  const reds     = team.filter(r => r.signal === 'red').length;
  const yellows  = team.length - greens - reds;
  const revColor = revPct >= 80 ? 'green' : revPct >= 40 ? 'amber' : 'red';
  const revFmt   = revenue >= 1000 ? '$' + Math.round(revenue/1000) + 'k' : '$' + revenue;
  document.getElementById('status-cards').innerHTML = `
    <div class="status-card">
      <div class="status-card-label">Revenue — Q1</div>
      <div class="status-card-value ${{revColor}}">${{revFmt}}</div>
      <div class="sb-bar"><div class="sb-bar-fill green" style="width:${{revPct}}%"></div></div>
      <div class="status-card-sub">${{revPct}}% of ${{Math.round(target/1000)}}k target</div>
    </div>
    <div class="status-card">
      <div class="status-card-label">1:1s This Week</div>
      <div class="status-card-value">${{oneDone}}/${{oneTotal}}</div>
      <div class="sb-bar"><div class="sb-bar-fill blue" style="width:${{onePct}}%"></div></div>
      <div class="status-card-sub">${{onePct}}% done</div>
    </div>
    <div class="status-card">
      <div class="status-card-label">Team Health</div>
      <div class="health-pills" style="margin-top:6px">
        ${{greens  ? `<span class="health-pill green">${{greens}}&nbsp;🟢</span>` : ''}}
        ${{yellows ? `<span class="health-pill amber">${{yellows}}&nbsp;🟡</span>` : ''}}
        ${{reds    ? `<span class="health-pill red">${{reds}}&nbsp;🔴</span>`    : ''}}
      </div>
      <div class="status-card-sub" style="margin-top:8px">${{team.length}} reps total</div>
    </div>
    <div class="status-card">
      <div class="status-card-label">Open Actions</div>
      <div class="status-card-value ${{actions > 0 ? 'amber' : 'green'}}">${{actions}}</div>
      <div class="status-card-sub">tracked in progress.md</div>
    </div>
    <div class="status-card">
      <div class="status-card-label">Side Quest</div>
      <div class="status-card-value">${{t1}}%</div>
      <div class="sb-bar"><div class="sb-bar-fill amber" style="width:${{t1}}%"></div></div>
      <div class="status-card-sub">Track 2: ${{t2}}% · ${{shStatus}}</div>
    </div>
  `;
  document.getElementById('sb-updated').textContent = 'Generated ' + DATA.generated;

  // ── Activity / recent updates bar ────────────────────────────────────
  (function() {{
    const bar = document.getElementById('activity-bar');
    const recent = (DATA.team || [])
      .filter(r => r.last_session && r.last_session !== '—' && r.last_session !== 'No sessions')
      .sort((a, b) => {{
        // Sort by most recent (parse "DD Month YYYY" dates roughly)
        const months = {{jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12}};
        function parseDate(s) {{
          const p = (s||'').toLowerCase().split(' ');
          if (p.length >= 3) return new Date(p[2], (months[p[1]?.slice(0,3)]||1)-1, parseInt(p[0])||1);
          return new Date(0);
        }}
        return parseDate(b.last_session) - parseDate(a.last_session);
      }})
      .slice(0, 5);

    if (!recent.length) return;

    const sigEmoji = {{ green: '🟢', yellow: '🟡', amber: '🟡', red: '🔴', unknown: '⚪' }};
    const escA = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

    bar.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;padding:8px 0 12px 0;';
    bar.innerHTML = '<div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#f59e0b;font-family:var(--mono);font-weight:700;width:100%;padding-bottom:2px;">🔔 Recent Updates</div>'
      + recent.map(r => `
        <div style="display:flex;align-items:center;gap:6px;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.25);border-radius:20px;padding:4px 12px;font-size:11px;font-family:var(--mono);cursor:pointer;" onclick="toggleRepNotes('${{escA(r.id)}}')">
          ${{sigEmoji[r.signal] || '⚪'}}
          <span style="color:var(--text1);font-weight:600;">${{escA(r.name.split(' ')[0])}}</span>
          <span style="color:var(--text3)">·</span>
          <span style="color:var(--text2)">${{escA(r.last_session)}}</span>
          ${{r.rep_actions?.length ? `<span style="background:rgba(245,158,11,0.2);color:#f59e0b;border-radius:10px;padding:1px 6px;font-size:10px;">${{r.rep_actions.length}} actions</span>` : ''}}
        </div>`).join('');
  }})();

  // ── Team status table ────────────────────────────────────────────────
  const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  let rows = '';
  let totalRepActions = 0;
  let tG = 0, tY = 0, tR = 0;
  (DATA.team || []).forEach(rep => {{
    const sig = rep.signal || 'unknown';
    if (sig === 'green') tG++;
    else if (sig === 'red') tR++;
    else tY++;
    const repActions = rep.rep_actions || [];
    totalRepActions += repActions.length;
    const actionsHtml = repActions.length
      ? repActions.map(a => `<div class="tst-action-item">${{esc(a)}}</div>`).join('')
      : `<span style="color:var(--text3);font-size:11px">—</span>`;
    const sessionLine = [rep.last_session, rep.last_session_type].filter(Boolean).join(' · ');
    // Notes panel entries
    const entries = rep.entries || [];
    const notesHtml = entries.length
      ? entries.map(e => `<div class="notes-entry">
          <div class="notes-entry-title">${{esc(e.title)}}</div>
          <div class="notes-entry-body">${{esc(e.body)}}</div>
        </div>`).join('')
      : `<div style="color:var(--text3);font-size:12px">No entries found</div>`;
    rows += `<tr>
      <td>
        <div class="tst-name">${{esc(rep.name)}}</div>
        <button class="notes-toggle-btn" id="notes-btn-${{rep.id}}" onclick="toggleNotes('${{rep.id}}')" style="margin-top:5px">📖 Notes</button>
      </td>
      <td>
        <div class="tst-signal">
          <span class="tst-sig-dot ${{sig}}"></span>
          <span class="tst-sig-text">${{esc(rep.signal_text || sig)}}</span>
        </div>
        ${{rep.signal_reason ? `<div style="font-size:11px;color:var(--text3);margin-top:4px;line-height:1.5">${{esc(rep.signal_reason)}}</div>` : ''}}
      </td>
      <td class="tst-session">${{esc(sessionLine || '—')}}</td>
      <td class="tst-actions">${{actionsHtml}}</td>
      <td>
        <div class="quick-add-row">
          <select class="qa-select" id="qa-type-${{rep.id}}">
            <option value="note">📝 Note</option>
            <option value="action">⚡ Action</option>
            <option value="response">💬 Response</option>
            <option value="closed">✅ Closed</option>
          </select>
          <input class="qa-input" id="qa-input-${{rep.id}}"
            placeholder="Add note, action or response…"
            onkeydown="if(event.key==='Enter')addNote('${{rep.id}}')">
          <button class="qa-btn" onclick="addNote('${{rep.id}}')">Add</button>
        </div>
        <div class="qa-feedback" id="qa-fb-${{rep.id}}"></div>
      </td>
    </tr>
    <tr class="notes-panel-row" id="notes-row-${{rep.id}}">
      <td colspan="5">
        <div class="notes-panel" id="notes-panel-${{rep.id}}">
          <div class="notes-panel-inner">${{notesHtml}}</div>
        </div>
      </td>
    </tr>`;
  }});
  document.getElementById('team-status-table').innerHTML =
    `<thead><tr>
      <th style="width:110px">Rep</th>
      <th style="width:200px">Signal</th>
      <th style="width:170px">Last Session</th>
      <th>Open Actions</th>
      <th style="width:300px">Quick Add</th>
    </tr></thead><tbody>${{rows}}</tbody>`;

  // ── EMEA summary section ─────────────────────────────────────────────
  const revPctV  = Math.min(100, Math.round((p.TOPTAL_REVENUE||0) / (p.TOPTAL_TARGET||624270) * 100));
  const oneDoneV = p.TOPTAL_1ON1S_DONE  || 0;
  const oneTotV  = p.TOPTAL_1ON1S_TOTAL || 6;
  const h       = DATA.ops_highlights || {{}};
  const rskItems = h.risks    || [];
  const winItems = h.wins     || [];

  // Manager todos: from rep logs (Michael: commitments) + ops-log
  const managerTodos = DATA.manager_todos || [];
  const mgrDoneKey = 'mgrTodoDone';
  const mgrDone    = JSON.parse(localStorage.getItem(mgrDoneKey) || '{{}}');
  function mgrTodoId(t) {{ return (t.rep_id || t.rep) + '::' + t.action; }}
  function toggleMgrTodo(todoId) {{
    mgrDone[todoId] = !mgrDone[todoId];
    localStorage.setItem(mgrDoneKey, JSON.stringify(mgrDone));
    renderMgrTodos();
  }}
  function renderMgrTodos() {{
    const col = document.getElementById('mgr-todo-col');
    if (!col) return;
    const open     = managerTodos.filter(t => !mgrDone[mgrTodoId(t)]);
    const done     = managerTodos.filter(t =>  mgrDone[mgrTodoId(t)]);
    const makeItem = (t, isDone) => {{
      const tid = mgrTodoId(t).replace(/"/g,'&quot;');
      return `<div class="ops-item action" style="display:flex;align-items:flex-start;gap:8px;${{isDone ? 'opacity:0.45;' : ''}}">
        <button onclick="toggleMgrTodo('${{tid}}')"
          style="flex-shrink:0;margin-top:1px;width:16px;height:16px;border-radius:3px;border:1px solid ${{isDone ? 'var(--green)' : 'var(--text3)'}};background:${{isDone ? 'var(--green)' : 'transparent'}};color:#000;font-size:10px;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;"
          title="${{isDone ? 'Mark incomplete' : 'Mark complete'}}">${{isDone ? '✓' : ''}}</button>
        <div style="flex:1;min-width:0;">
          <span style="${{isDone ? 'text-decoration:line-through;' : ''}}">${{esc(t.action)}}</span>
          ${{t.rep !== 'Team' ? `<div style="font-size:10px;color:var(--text3);font-family:var(--mono)">${{esc(t.rep)}}${{t.date ? ' · ' + esc(t.date) : ''}}</div>` : ''}}
        </div>
      </div>`;
    }};
    let html = open.map(t => makeItem(t, false)).join('');
    if (done.length) {{
      html += `<div style="font-size:10px;color:var(--text3);font-family:var(--mono);margin:8px 0 4px;text-transform:uppercase;letter-spacing:0.06em;">✓ Done this week (${{done.length}})</div>`;
      html += done.map(t => makeItem(t, true)).join('');
    }}
    if (!html) html = `<div class="ops-empty">No manager actions logged</div>`;
    col.innerHTML = `<div class="emea-col-label">➡️ Manager To-Do <span style="font-size:10px;color:var(--text3);font-family:var(--mono);margin-left:6px">from 1:1 logs</span></div>` + html;
  }}

  // Patterns: from individual rep logs (Pattern note) + ops-log patterns
  const repPatterns = DATA.team
    .filter(r => r.pattern_note)
    .map(r => `<div class="ops-item pattern" style="display:flex;flex-direction:column;gap:2px;">
      <span>${{esc(r.pattern_note)}}</span>
      <span style="font-size:10px;color:var(--text3);font-family:var(--mono)">${{esc(r.name)}} · ${{esc(r.last_session || '')}}</span>
    </div>`);
  const obsItems = [
    ...repPatterns,
    ...rskItems.map(t => `<div class="ops-item risk">${{esc(t)}}</div>`),
    ...winItems.map(t => `<div class="ops-item win">${{esc(t)}}</div>`),
  ].join('') || `<div class="ops-empty">No patterns or risks flagged</div>`;

  document.getElementById('emea-section').innerHTML = `
    <div class="emea-col">
      <div class="emea-col-label">🌍 EMEA Total</div>
      <div class="health-pills" style="margin-bottom:10px">
        ${{tG ? `<span class="health-pill green">${{tG}}&nbsp;🟢</span>` : ''}}
        ${{tY ? `<span class="health-pill amber">${{tY}}&nbsp;🟡</span>` : ''}}
        ${{tR ? `<span class="health-pill red"  >${{tR}}&nbsp;🔴</span>` : ''}}
      </div>
      <div class="emea-stat-row"><span class="emea-stat-label">Revenue</span><span class="emea-stat-value">${{revPctV}}%</span></div>
      <div class="emea-stat-row"><span class="emea-stat-label">1:1s</span><span class="emea-stat-value">${{oneDoneV}}/${{oneTotV}}</span></div>
      <div class="emea-stat-row"><span class="emea-stat-label">Rep actions</span><span class="emea-stat-value">${{totalRepActions}}</span></div>
      <div class="emea-stat-row"><span class="emea-stat-label">Open actions</span><span class="emea-stat-value ${{(p.TOPTAL_OPEN_ACTIONS||0) > 0 ? 'amber' : ''}}">${{p.TOPTAL_OPEN_ACTIONS||0}}</span></div>
    </div>
    <div class="emea-col" id="mgr-todo-col"></div>
    <div class="emea-col">
      <div class="emea-col-label">🔁 Patterns &amp; Flags <span style="font-size:10px;color:var(--text3);font-family:var(--mono);margin-left:6px">from rep logs</span></div>
      ${{obsItems}}
    </div>
  `;
  renderMgrTodos(); // populate manager to-do column
  // Ops log accordion below EMEA section
  const opsLogEntries = DATA.ops_log || [];
  const escOps = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  let opsLogHtml = `<div style="margin-top:10px;border:1px solid var(--border);border-radius:6px;overflow:hidden">
    <div style="padding:8px 14px;background:var(--surface2);display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)">
      <span style="font-size:10px;text-transform:uppercase;letter-spacing:0.07em;color:var(--text3);font-family:var(--mono)">📋 Manager Ops Log — ${{opsLogEntries.length}} entries</span>
      <button class="notes-toggle-btn" id="opslog-toggle" onclick="toggleOpsLogSection()">View log</button>
    </div>
    <div id="opslog-section" style="max-height:0;overflow:hidden;transition:max-height 0.3s ease">`;
  opsLogEntries.forEach((entry, i) => {{
    opsLogHtml += `<div style="border-bottom:1px solid var(--border)">
      <div style="padding:8px 14px;cursor:pointer;display:flex;align-items:center;gap:8px;font-size:12px;font-family:var(--mono);color:var(--text2);background:var(--surface)" onclick="toggleEmeaEntry(${{i}})">
        <span id="emea-chev-${{i}}" style="font-size:9px;color:var(--text3);transition:transform 0.2s">▶</span>
        ${{escOps(entry.title)}}
      </div>
      <div id="emea-entry-${{i}}" style="max-height:0;overflow:hidden;transition:max-height 0.3s ease">
        <div style="padding:10px 16px;font-size:12px;color:var(--text2);line-height:1.65;white-space:pre-wrap;font-family:var(--mono);border-top:1px solid var(--border);background:var(--bg)">${{escOps(entry.body)}}</div>
      </div>
    </div>`;
  }});
  opsLogHtml += `</div></div>`;

  // Quick ops-log entry input
  opsLogHtml += `
  <div style="margin-top:10px;border:1px solid var(--border);border-radius:6px;overflow:hidden">
    <div style="padding:8px 14px;background:var(--surface2);border-bottom:1px solid var(--border)">
      <span style="font-size:10px;text-transform:uppercase;letter-spacing:0.07em;color:var(--text3);font-family:var(--mono)">✏️ Add Ops Log Entry</span>
    </div>
    <div style="padding:10px 14px;display:flex;flex-direction:column;gap:8px;">
      <textarea id="ops-entry-input" rows="3"
        style="width:100%;background:var(--bg);border:1px solid var(--border);border-radius:4px;color:var(--text1);font-size:12px;font-family:var(--mono);padding:8px;resize:vertical;line-height:1.5;"
        placeholder="Add a note, decision, pattern, or action item… Use ➡️ for actions, 🔁 for patterns, 🔴 for risks, ✅ for wins"></textarea>
      <div style="display:flex;gap:8px;align-items:center;">
        <input id="ops-entry-label" type="text" value="Team Note"
          style="width:160px;background:var(--bg);border:1px solid var(--border);border-radius:4px;color:var(--text2);font-size:11px;font-family:var(--mono);padding:5px 8px;"
          placeholder="Label (e.g. Team Note)">
        <button onclick="saveOpsEntry()"
          style="background:var(--surface2);border:1px solid var(--border);border-radius:4px;color:var(--text1);font-size:11px;font-family:var(--mono);padding:5px 14px;cursor:pointer;">
          💾 Save to Ops Log
        </button>
        <span id="ops-save-status" style="font-size:11px;color:var(--green);font-family:var(--mono);display:none">✓ Saved</span>
      </div>
    </div>
  </div>`;

  document.getElementById('emea-section').insertAdjacentHTML('afterend', opsLogHtml);
}})();

function toggleOpsLogSection() {{
  const el  = document.getElementById('opslog-section');
  const btn = document.getElementById('opslog-toggle');
  if (!el) return;
  const open = el.style.maxHeight !== '0px' && el.style.maxHeight !== '';
  el.style.maxHeight = open ? '0' : '2000px';
  btn.textContent = open ? 'View log' : 'Close';
  btn.classList.toggle('open', !open);
}}
function toggleEmeaEntry(i) {{
  const el   = document.getElementById('emea-entry-' + i);
  const chev = document.getElementById('emea-chev-'  + i);
  if (!el) return;
  const open = el.style.maxHeight !== '0px' && el.style.maxHeight !== '';
  el.style.maxHeight = open ? '0' : '1000px';
  if (chev) chev.style.transform = open ? 'rotate(0deg)' : 'rotate(90deg)';
}}

function toggleNotes(repId) {{
  const panel = document.getElementById('notes-panel-' + repId);
  const btn   = document.getElementById('notes-btn-'  + repId);
  if (!panel) return;
  const isOpen = panel.classList.contains('open');
  panel.classList.toggle('open', !isOpen);
  btn.classList.toggle('open', !isOpen);
  btn.textContent = isOpen ? '📖 Notes' : '📖 Close';
}}

async function saveOpsEntry() {{
  const text  = (document.getElementById('ops-entry-input')?.value || '').trim();
  const label = (document.getElementById('ops-entry-label')?.value || 'Team Note').trim();
  const statusEl = document.getElementById('ops-save-status');
  if (!text) {{ showToast('Add some text first'); return; }}
  try {{
    const res = await fetch('http://localhost:5678/api/save-ops-log', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ summary: text, label }})
    }});
    const data = await res.json();
    if (data.ok) {{
      document.getElementById('ops-entry-input').value = '';
      if (statusEl) {{ statusEl.style.display = 'inline'; setTimeout(() => statusEl.style.display = 'none', 3000); }}
      showToast('✅ Saved to ops log');
    }} else {{
      showToast('⚠️ ' + (data.error || 'Save failed'));
    }}
  }} catch(e) {{
    showToast('⚠️ Server offline');
  }}
}}

async function addNote(repId) {{
  const typeEl  = document.getElementById('qa-type-' + repId);
  const inputEl = document.getElementById('qa-input-' + repId);
  const fbEl    = document.getElementById('qa-fb-'   + repId);
  const text    = inputEl.value.trim();
  const type    = typeEl ? typeEl.value : 'note';
  if (!text) {{ inputEl.focus(); return; }}
  const btnEl = inputEl.nextElementSibling;
  btnEl.disabled = true; btnEl.textContent = '…';
  try {{
    const res  = await fetch('http://localhost:5678/api/add-note', {{
      method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ repId, type, text }})
    }});
    const data = await res.json();
    if (data.ok) {{
      inputEl.value = '';
      fbEl.textContent = '✓ Saved';
      fbEl.style.display = 'block';
      showToast('\u2713 Saved to ' + repId + '\u2019s log', 2000);
      setTimeout(() => {{ fbEl.style.display = 'none'; }}, 2500);
    }} else {{
      showToast('⚠️ ' + (data.error || 'Save failed'), 3000);
    }}
  }} catch(e) {{
    showToast('⚠️ Server offline — run dashboard/server.py', 3000);
  }}
  btnEl.disabled = false; btnEl.textContent = 'Add';
}}

// ── Top bar ───────────────────────────────────────────────────────────────
document.getElementById('tb-week').textContent    = 'Wk' + DATA.week;
document.getElementById('tb-q1').textContent      = DATA.q1_pct + '%';
document.getElementById('tb-1on1').textContent    = DATA.one_on_ones;
document.getElementById('tb-actions').textContent = DATA.open_actions + ' actions';
document.getElementById('tb-date').textContent    = DATA.date_label;
document.getElementById('footer-gen').textContent = DATA.generated;

// ── Toptal panel ──────────────────────────────────────────────────────────
const p = DATA.progress;
const revenue = p.TOPTAL_REVENUE || 0;
const target  = p.TOPTAL_TARGET  || 624270;
const revPct  = target > 0 ? (revenue / target) * 100 : 0;
document.getElementById('val-revenue').textContent = '$' + fmt(revenue) + ' / $' + fmt(target) + ' (' + DATA.revenue_pct + '%)';
document.getElementById('toptal-badge').textContent = DATA.revenue_pct + '% to target';
setBar('bar-revenue', revPct);

const done  = p.TOPTAL_1ON1S_DONE  || 0;
const total = p.TOPTAL_1ON1S_TOTAL || 6;
const on1Pct = total > 0 ? (done / total) * 100 : 0;
document.getElementById('val-1on1').textContent = done + ' of ' + total + ' this week';
setBar('bar-1on1', on1Pct);

document.getElementById('val-actions').textContent = p.TOPTAL_OPEN_ACTIONS || 0;

// ── Team grid ─────────────────────────────────────────────────────────────
const grid = document.getElementById('team-grid');
const signalEmoji = {{ green: '💪', amber: '👀', red: '🚨', unknown: '❓' }};
DATA.team.forEach(rep => {{
  const card = document.createElement('div');
  card.className = 'rep-card signal-' + rep.signal;

  const actionsHtml = (rep.rep_actions || []).length > 0
    ? rep.rep_actions.map(a => `<div class="rep-action-bullet">${{a}}</div>`).join('')
    : '<div class="rep-action-bullet" style="color:var(--text3);font-style:italic">None logged</div>';

  const sessionFooter = [rep.last_session, rep.last_session_type].filter(Boolean).join(' · ');
  card.innerHTML = `
    <div class="rep-card-top">
      <div class="rep-name">${{rep.name}}</div>
      <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
        <div class="signal-dot ${{rep.signal}}"></div>
        <span class="rep-chevron">▼</span>
      </div>
    </div>
    <div class="rep-signal-label ${{rep.signal}}">${{signalEmoji[rep.signal] || '—'}} ${{rep.signal_text}}</div>
    <div class="rep-expand">
      <div class="rep-expand-inner">
        ${{rep.signal_reason ? `
          <div class="rep-flag ${{rep.signal}}">
            <div class="rep-expand-label">Status</div>
            <div class="rep-flag-text">${{rep.signal_reason}}</div>
          </div>` : ''}}
        <div>
          <div class="rep-expand-label">Open actions (rep)</div>
          ${{actionsHtml}}
        </div>
        <div class="rep-expand-footer">
          <span>${{sessionFooter || '—'}}</span>
          <button class="rep-1on1-btn" onclick="event.stopPropagation();copyToClipboard('/1on1 ${{rep.name}}','Copied /1on1 ${{rep.name}}')">⟶ /1on1</button>
        </div>
      </div>
    </div>
  `;
  card.addEventListener('click', () => card.classList.toggle('expanded'));
  grid.appendChild(card);
}});

// ── Side hustle panel ─────────────────────────────────────────────────────
const t1 = p.SH_TRACK1_PCT || 0;
const t2 = p.SH_TRACK2_PCT || 0;
document.getElementById('val-t1').textContent = t1 + '%';
document.getElementById('val-t2').textContent = t2 + '%';
setBar('bar-t1', t1);
setBar('bar-t2', t2);
document.getElementById('sh-published').textContent = p.SH_POSTS_PUBLISHED || 0;
document.getElementById('sh-drafted').textContent   = p.SH_POSTS_DRAFTED   || 0;
document.getElementById('sh-active').textContent    = p.SH_ACTIVE_PIECES   || 0;
document.getElementById('sh-status').textContent    = p.SH_STATUS          || 'building';
document.getElementById('sh-badge').textContent     = p.SH_STATUS          || 'building';

// ── Sidebar ───────────────────────────────────────────────────────────────
const sidebar = document.getElementById('sidebar');
let lastGroup = '';
DATA.commands.forEach(c => {{
  if (c.group !== lastGroup) {{
    if (lastGroup !== '') {{
      const div = document.createElement('div');
      div.className = 'sidebar-divider';
      sidebar.appendChild(div);
    }}
    const label = document.createElement('div');
    label.className = 'sidebar-group-label';
    label.textContent = c.group;
    sidebar.appendChild(label);
    lastGroup = c.group;
  }}
  const btn = document.createElement('button');
  btn.className = 'cmd-btn';
  const full = c.args ? c.cmd + ' ' + c.args : c.cmd;
  btn.innerHTML = `
    <span class="cmd-name">${{c.cmd}}<span class="cmd-args"> ${{c.args}}</span></span>
    <span class="cmd-desc">${{c.desc}}</span>
  `;
  btn.title = 'Click to copy: ' + full;
  btn.addEventListener('click', () => copyToClipboard(full, 'Copied: ' + c.cmd));
  sidebar.appendChild(btn);
}});

// ── This Week schedule ────────────────────────────────────────────────────
const CAT_COLORS  = DATA.categories || {{}};
const weekGrid    = document.getElementById('week-grid');
const taskState   = JSON.parse(localStorage.getItem('taskState')   || '{{}}');
const taskOrder   = JSON.parse(localStorage.getItem('taskOrder')   || '{{}}');
const customTasks = JSON.parse(localStorage.getItem('customTasks') || '{{}}');

function saveTaskState()   {{ localStorage.setItem('taskState',   JSON.stringify(taskState));   }}
function saveTaskOrder()   {{ localStorage.setItem('taskOrder',   JSON.stringify(taskOrder));   }}
function saveCustomTasks() {{ localStorage.setItem('customTasks', JSON.stringify(customTasks)); }}

document.getElementById('week-today-label').textContent =
  DATA.today_day.charAt(0).toUpperCase() + DATA.today_day.slice(1)
  + ' — click to done · drag to reorder · + to add';

// ── Drag state ─────────────────────────────────────────────────────────────
let dragSrcDay = null, dragSrcId = null;

function onDragStart(e, dayKey, taskId) {{
  dragSrcDay = dayKey; dragSrcId = taskId;
  setTimeout(() => e.currentTarget.classList.add('dragging'), 0);
  e.dataTransfer.effectAllowed = 'move';
}}
function onDragEnd(e) {{
  e.currentTarget.classList.remove('dragging');
  document.querySelectorAll('.drag-over').forEach(c => c.classList.remove('drag-over'));
}}
function onDragOver(e) {{
  e.preventDefault();
  document.querySelectorAll('.drag-over').forEach(c => c.classList.remove('drag-over'));
  e.currentTarget.classList.add('drag-over');
}}
function onDragLeave(e) {{ e.currentTarget.classList.remove('drag-over'); }}
function onDrop(e, dayKey, taskId) {{
  e.preventDefault();
  e.currentTarget.classList.remove('drag-over');
  if (!dragSrcId || dragSrcId === taskId || dragSrcDay !== dayKey) return;
  const container = document.getElementById('tasks-' + dayKey);
  const srcEl = container.querySelector('[data-task-id="' + dragSrcId + '"]');
  const tgtEl = e.currentTarget;
  if (srcEl && tgtEl && srcEl !== tgtEl) {{
    container.insertBefore(srcEl, tgtEl);
    taskOrder[dayKey] = [...container.querySelectorAll('.task-chip')].map(c => c.dataset.taskId);
    saveTaskOrder();
  }}
}}

// ── Render a single chip ───────────────────────────────────────────────────
function renderChip(task, dayKey) {{
  const container = document.getElementById('tasks-' + dayKey);
  const stateKey  = dayKey + ':' + task.id;
  const isDone    = taskState[stateKey] === 'done';
  const cat       = CAT_COLORS[task.category] || {{}};
  const chip      = document.createElement('div');
  chip.className  = 'task-chip' + (isDone ? ' done' : '') + (task.custom ? ' custom-task' : '');
  chip.dataset.taskId = task.id;
  chip.setAttribute('draggable', 'true');
  chip.style.background      = (cat.color || '#374151') + '22';
  chip.style.borderLeftColor = cat.color || '#374151';
  const icon = task.auto === true ? '⚡' : task.auto === 'partial' ? '◑' : (task.icon || '○');
  chip.innerHTML = `
    <span class="task-icon">${{icon}}</span>
    <span class="task-name">${{task.name}}</span>
    ${{task.custom ? `<button class="task-move-btn" title="Move to another day" onclick="showMoveMenu(event,'${{dayKey}}','${{task.id}}')">📅</button>` : ''}}
    ${{task.custom ? '<button class="task-delete-btn" title="Delete task">×</button>' : ''}}
    <div class="task-check">${{isDone ? '✓' : ''}}</div>
  `;
  // Toggle done (skip if click landed on delete btn)
  chip.addEventListener('click', e => {{
    if (e.target.classList.contains('task-delete-btn')) return;
    if (e.target.classList.contains('task-move-btn')) return;
    taskState[stateKey] = taskState[stateKey] === 'done' ? 'pending' : 'done';
    const done = taskState[stateKey] === 'done';
    chip.classList.toggle('done', done);
    chip.querySelector('.task-check').textContent = done ? '✓' : '';
    saveTaskState();
    if (done) {{
      chip.classList.add('just-done');
      setTimeout(() => chip.classList.remove('just-done'), 400);
      updateScore();
      const msg = getAchievementMsg();
      if (task.command) {{ copyToClipboard(task.command, msg + ' · Copied: ' + task.command); }}
      else {{ showToast(msg); }}
    }} else {{ updateScore(); }}
  }});
  // Delete (custom tasks only)
  if (task.custom) {{
    chip.querySelector('.task-delete-btn').addEventListener('click', e => {{
      e.stopPropagation();
      customTasks[dayKey] = (customTasks[dayKey] || []).filter(t => t.id !== task.id);
      saveCustomTasks();
      chip.style.transition = 'all 0.18s';
      chip.style.opacity    = '0';
      chip.style.transform  = 'scale(0.85)';
      setTimeout(() => chip.remove(), 200);
    }});
  }}
  // Drag events
  chip.addEventListener('dragstart', e => onDragStart(e, dayKey, task.id));
  chip.addEventListener('dragend',   e => onDragEnd(e));
  chip.addEventListener('dragover',  e => onDragOver(e));
  chip.addEventListener('dragleave', e => onDragLeave(e));
  chip.addEventListener('drop',      e => onDrop(e, dayKey, task.id));
  // Insert before the + button if present
  const addBtn = container.querySelector('.add-task-btn');
  if (addBtn) container.insertBefore(chip, addBtn); else container.appendChild(chip);
}}

// ── Move task to a different day ──────────────────────────────────────────
function moveTaskToDay(fromDay, taskId, toDay) {{
  if (fromDay === toDay) return;
  const task = (customTasks[fromDay] || []).find(t => t.id === taskId);
  if (!task) return;
  // Remove from old day
  customTasks[fromDay] = (customTasks[fromDay] || []).filter(t => t.id !== taskId);
  // Remove any done state on old day
  delete taskState[fromDay + ':' + taskId];
  // Add to new day
  if (!customTasks[toDay]) customTasks[toDay] = [];
  customTasks[toDay].push(task);
  saveCustomTasks();
  saveTaskState();
  // Re-render both days
  [fromDay, toDay].forEach(day => {{
    const container = document.getElementById('tasks-' + day);
    if (!container) return;
    // Clear chips and re-render
    [...container.querySelectorAll('.task-chip')].forEach(c => c.remove());
    const base   = (DATA.schedule.find(d => d.day === day) || {{}}).tasks || [];
    const custom = customTasks[day] || [];
    [...base, ...custom].forEach(t => renderChip(t, day));
  }});
  showToast('📅 Moved to ' + toDay.charAt(0).toUpperCase() + toDay.slice(1));
}}

function showMoveMenu(e, fromDay, taskId) {{
  e.stopPropagation();
  // Remove any existing menu
  document.querySelectorAll('.move-day-menu').forEach(m => m.remove());
  const days = DATA.schedule.map(d => d.day).filter(d => d !== fromDay);
  const menu = document.createElement('div');
  menu.className = 'move-day-menu';
  menu.style.cssText = 'position:absolute;z-index:999;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:4px;box-shadow:0 4px 16px rgba(0,0,0,0.4);font-size:11px;font-family:var(--mono);';
  menu.innerHTML = days.map(d =>
    `<div onclick="moveTaskToDay('${{fromDay}}','${{taskId}}','${{d}}');this.closest('.move-day-menu').remove();"
      style="padding:5px 12px;cursor:pointer;border-radius:4px;color:var(--text1);"
      onmouseover="this.style.background='var(--surface)'"
      onmouseout="this.style.background=''">${{d.charAt(0).toUpperCase() + d.slice(1)}}</div>`
  ).join('');
  const rect = e.target.getBoundingClientRect();
  menu.style.top  = (rect.bottom + window.scrollY + 4) + 'px';
  menu.style.left = rect.left + 'px';
  document.body.appendChild(menu);
  setTimeout(() => document.addEventListener('click', () => menu.remove(), {{ once: true }}), 0);
}}

// ── Add task inline input ──────────────────────────────────────────────────
function startAddTask(dayKey) {{
  const container = document.getElementById('tasks-' + dayKey);
  if (container.querySelector('.add-task-input')) return; // already open
  const empty = container.querySelector('.empty-day');
  if (empty) empty.remove();
  const input   = document.createElement('input');
  input.type    = 'text';
  input.className   = 'add-task-input';
  input.placeholder = 'Task name… Enter to save · Esc to cancel';
  const addBtn  = container.querySelector('.add-task-btn');
  container.insertBefore(input, addBtn || null);
  input.focus();
  let saved = false;
  function commit() {{
    if (saved) return; saved = true;
    const name = input.value.trim();
    input.remove();
    if (!name) return;
    if (!customTasks[dayKey]) customTasks[dayKey] = [];
    const t = {{ id: 'custom-' + Date.now(), name, icon: '📌', auto: false, custom: true }};
    customTasks[dayKey].push(t);
    saveCustomTasks();
    renderChip(t, dayKey);
    showToast('✅ Added: ' + name);
  }}
  input.addEventListener('keydown', e => {{
    if (e.key === 'Enter')  {{ e.preventDefault(); commit(); }}
    if (e.key === 'Escape') {{ saved = true; input.remove(); }}
  }});
  input.addEventListener('blur', () => setTimeout(commit, 100));
}}

// ── Build all day columns ──────────────────────────────────────────────────
DATA.schedule.forEach(day => {{
  const col = document.createElement('div');
  col.className = 'day-col' + (day.is_today ? ' today' : '');
  const todayBadge = day.is_today ? '<span class="today-badge">TODAY</span>' : '';
  col.innerHTML = `<div class="day-header"><span>${{day.label}}</span>${{todayBadge}}</div><div class="day-tasks" id="tasks-${{day.day}}"></div>`;
  weekGrid.appendChild(col);

  const container = col.querySelector('.day-tasks');
  const base   = day.tasks || [];
  const custom = customTasks[day.day] || [];
  const all    = [...base, ...custom];
  const order  = taskOrder[day.day];

  // Sort by saved order, append anything new at end
  let ordered = all;
  if (order && order.length > 0) {{
    const map = {{}};
    all.forEach(t => {{ map[t.id] = t; }});
    ordered = order.map(id => map[id]).filter(Boolean);
    const inOrder = new Set(order);
    all.forEach(t => {{ if (!inOrder.has(t.id)) ordered.push(t); }});
  }}

  if (ordered.length === 0) {{
    container.innerHTML = '<div class="empty-day">Click + to add a task</div>';
  }} else {{
    ordered.forEach(task => renderChip(task, day.day));
  }}

  // "+" add task button
  const addBtn = document.createElement('button');
  addBtn.className = 'add-task-btn';
  addBtn.textContent = '+ Add task';
  addBtn.addEventListener('click', () => startAddTask(day.day));
  container.appendChild(addBtn);

  // Click on empty space also opens the add input
  container.addEventListener('click', e => {{
    if (e.target === container || e.target.classList.contains('empty-day')) {{
      startAddTask(day.day);
    }}
  }});
}});

// ── Daily score + achievement toasts ──────────────────────────────────────
const TODAY_KEY = DATA.today_day;
const achieveMsgs = [
  '⚡ Done!', '🔥 Crushing it!', '✅ Smashed!', '💥 One down!',
  '🎯 On target!', '🚀 Keep going!', '🏆 You legend!', '⚡ Next!',
];
let achIdx = 0;
function getAchievementMsg() {{
  return achieveMsgs[achIdx++ % achieveMsgs.length];
}}
function getScore() {{
  return Object.entries(taskState)
    .filter(([k, v]) => k.startsWith(TODAY_KEY + ':') && v === 'done')
    .length;
}}
function updateScore() {{
  const score = getScore();
  const el = document.getElementById('tb-score');
  if (el) el.textContent = score + ' pts';
}}
updateScore(); // set on load

// ── Rollover: undone custom tasks from past days → today ──────────────────
(function() {{
  const days   = DATA.schedule.map(d => d.day);
  const todayI = days.indexOf(TODAY_KEY);
  if (todayI <= 0) return; // nothing before today to roll over
  const pastDays = days.slice(0, todayI);
  const todayContainer = document.getElementById('tasks-' + TODAY_KEY);
  if (!todayContainer) return;
  const rolled = [];
  pastDays.forEach(pastDay => {{
    (customTasks[pastDay] || []).forEach(task => {{
      const stateKey = pastDay + ':' + task.id;
      if (taskState[stateKey] !== 'done') rolled.push({{ task, pastDay }});
    }});
  }});
  if (!rolled.length) return;
  // Add a divider
  const divider = document.createElement('div');
  divider.style.cssText = 'font-size:10px;color:var(--text3);font-family:var(--mono);padding:4px 2px 2px;text-transform:uppercase;letter-spacing:0.06em;';
  divider.textContent = '↩ Carried forward';
  const addBtn = todayContainer.querySelector('.add-task-btn');
  if (addBtn) todayContainer.insertBefore(divider, addBtn); else todayContainer.appendChild(divider);
  rolled.forEach(({{ task, pastDay }}) => {{
    // Render as a rollover chip using the past day's state key
    const stateKey = pastDay + ':' + task.id;
    const isDone   = taskState[stateKey] === 'done';
    const chip     = document.createElement('div');
    chip.className = 'task-chip' + (isDone ? ' done' : '') + ' custom-task';
    chip.dataset.taskId = 'roll:' + pastDay + ':' + task.id;
    chip.style.cssText  = 'border-left-color:#6366f1;opacity:0.85;';
    chip.innerHTML = `
      <span class="task-icon">↩</span>
      <span class="task-name">${{task.name}}</span>
      <span style="font-size:9px;color:var(--text3);font-family:var(--mono);margin-left:2px">${{pastDay.slice(0,3)}}</span>
      <button class="task-move-btn" title="Move to another day" onclick="showMoveMenu(event,'${{pastDay}}','${{task.id}}')">📅</button>
      <div class="task-check">${{isDone ? '✓' : ''}}</div>
    `;
    chip.addEventListener('click', e => {{
      if (e.target.classList.contains('task-move-btn')) return;
      taskState[stateKey] = taskState[stateKey] === 'done' ? 'pending' : 'done';
      const done = taskState[stateKey] === 'done';
      chip.classList.toggle('done', done);
      chip.querySelector('.task-check').textContent = done ? '✓' : '';
      saveTaskState();
      if (done) {{
        chip.classList.add('just-done');
        setTimeout(() => chip.classList.remove('just-done'), 400);
        updateScore();
        showToast(getAchievementMsg());
      }} else {{ updateScore(); }}
    }});
    if (addBtn) todayContainer.insertBefore(chip, addBtn); else todayContainer.appendChild(chip);
  }});
}})();

// ── Inject meeting prep into week grid ────────────────────────────────────
DATA.meeting_prep.forEach(prep => {{
  const dayKey = (prep.dueDay || '').toLowerCase();
  const container = document.getElementById('tasks-' + dayKey);
  if (!container) return;
  const chip = document.createElement('div');
  chip.className = 'task-chip';
  chip.style.cssText = 'border-left:3px solid #6366f1;opacity:0.9;';
  chip.innerHTML = `<span class="chip-icon">📊</span><span class="chip-name">${{esc(prep.name)}} prep</span>`;
  chip.title = prep.name + ' · Due ' + prep.dueDay + ' ' + prep.dueTime;
  if (prep.slideUrl) chip.addEventListener('click', () => window.open(prep.slideUrl, '_blank'));
  const addBtn = container.querySelector('.add-task-btn');
  if (addBtn) container.insertBefore(chip, addBtn); else container.appendChild(chip);
}});

// ── Meeting Prep ──────────────────────────────────────────────────────────
const prepList = document.getElementById('prep-list');
DATA.meeting_prep.forEach(prep => {{
  const card = document.createElement('div');
  card.className = 'prep-card';
  const slidesHtml = prep.slides.map(s =>
    `<div class="prep-slide-row"><span class="prep-slide-num">S${{s.slide}}</span><span>${{s.content}}</span></div>`
  ).join('');
  const autoHtml = (prep.autoItems || []).map(a =>
    `<span class="auto-chip">⚡ ${{a}}</span>`
  ).join('');
  const freq = prep.frequency === 'biweekly' ? 'Bi-weekly' : 'Weekly';
  card.innerHTML = `
    <div>
      <div class="prep-name">${{prep.name}}</div>
      <div class="prep-meta">${{freq}} · Due ${{prep.dueDay.charAt(0).toUpperCase() + prep.dueDay.slice(1)}} ${{prep.dueTime}}</div>
      <div class="prep-slides">${{slidesHtml}}</div>
      <div class="prep-auto-chips">${{autoHtml}}</div>
    </div>
    <div class="prep-actions">
      <span class="prep-status ${{prep.status}}">${{prep.status.toUpperCase()}}</span>
      ${{prep.slideUrl ? `<button class="prep-open-btn" onclick="window.open('${{prep.slideUrl}}','_blank')">Open Slides ↗</button>` : ''}}
    </div>
  `;
  prepList.appendChild(card);
}});

// ── Metric updater ────────────────────────────────────────────────────────
const sel = document.getElementById('update-field');
DATA.fields.forEach(f => {{
  const opt = document.createElement('option');
  opt.value = f.key;
  opt.textContent = f.label;
  sel.appendChild(opt);
}});

function generateUpdateCmd() {{
  const field = document.getElementById('update-field').value;
  const value = document.getElementById('update-value').value.trim();
  if (!value) {{ showToast('Enter a value first'); return; }}
  const cmd = `/progress update ${{field}} ${{value}}`;
  document.getElementById('cmd-text').textContent = cmd;
  document.getElementById('cmd-output').style.display = 'block';
}}

function copyCmdOutput() {{
  const cmd = document.getElementById('cmd-text').textContent;
  copyToClipboard(cmd, 'Command copied — paste into Claude');
}}

// Allow Enter key in value input to trigger generate
document.getElementById('update-value').addEventListener('keydown', e => {{
  if (e.key === 'Enter') generateUpdateCmd();
}});

// ── Transcript Inbox ───────────────────────────────────────────────────────
const txState = JSON.parse(localStorage.getItem('txState') || '{{}}');

function saveTxState() {{
  localStorage.setItem('txState', JSON.stringify(txState));
}}

// All tabs: reps + huddle
const ALL_TABS = [
  ...DATA.team.map(r => ({{ ...r, type: 'rep' }})),
  {{ id: 'huddle', name: '🗓 Huddle', type: 'huddle' }},
  {{ id: 'adhoc',  name: '⚡ Ad Hoc', type: 'adhoc'  }}
];

const repTabsEl   = document.getElementById('rep-tabs');
const txPanelsEl  = document.getElementById('transcript-panels');

ALL_TABS.forEach((tab, idx) => {{
  const isHuddle     = tab.type === 'huddle';
  const isAdhoc      = tab.type === 'adhoc';
  const inputLabel   = isHuddle ? 'Paste huddle notes or agenda' : isAdhoc ? 'Paste any transcript' : 'Paste 1:1 transcript';
  const outputLabel  = 'Claude output';
  const inputHint    = isHuddle ? 'Paste huddle notes or agenda here...' : isAdhoc ? 'Paste any transcript here...' : 'Paste the call transcript here...';
  const outputHint   = isHuddle ? 'Generated huddle summary will appear here...' : isAdhoc ? 'Generated summary will appear here...' : 'Generated /summary will appear here...';
  const saveLabel    = isHuddle ? '💾 Save to ops-log' : '💾 Save to log';

  // Tab button
  const btn = document.createElement('button');
  btn.className = 'rep-tab-btn' + (idx === 0 ? ' active' : '') + (isHuddle ? ' huddle-tab' : '') + (isAdhoc ? ' adhoc-tab' : '');
  btn.textContent = tab.name;
  btn.dataset.tabId = tab.id;
  btn.addEventListener('click', () => switchTab(tab.id));
  repTabsEl.appendChild(btn);

  const savedTx  = (txState[tab.id] || {{}}).transcript || '';
  const savedOut = (txState[tab.id] || {{}}).output     || '';

  // Content panel (two-column grid)
  const panel = document.createElement('div');
  panel.className = 'transcript-content';
  panel.id = 'tx-panel-' + tab.id;
  if (idx === 0) panel.style.display = 'grid';

  panel.innerHTML = `
    <div class="transcript-col">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
        <div class="transcript-col-label" style="margin-bottom:0">${{inputLabel}}</div>
        <button class="voice-btn-inline" id="voice-btn-${{tab.id}}" onclick="startVoice('${{tab.id}}')" title="Dictate into transcript">🎤 Voice</button>
      </div>
      <textarea class="transcript-textarea" id="tx-input-${{tab.id}}"
        placeholder="${{inputHint}}"
        oninput="onTxInput('${{tab.id}}')">${{savedTx}}</textarea>
    </div>
    <div class="transcript-col">
      <div class="transcript-col-label">${{outputLabel}}</div>
      <div class="tx-name-warning" id="tx-warning-${{tab.id}}"></div>
      <textarea class="transcript-textarea" id="tx-output-${{tab.id}}"
        placeholder="${{outputHint}}"
        oninput="onTxOutput('${{tab.id}}')">${{savedOut}}</textarea>
      <div class="transcript-output-actions">
        <button class="t-btn slack" onclick="copySlackMessage('${{tab.id}}')">Copy as Slack Message</button>
      </div>
    </div>
  `;
  txPanelsEl.appendChild(panel);

  // Action bar below the columns
  const bar = document.createElement('div');
  bar.className = 'transcript-action-bar';
  bar.id = 'tx-bar-' + tab.id;
  if (idx !== 0) bar.style.display = 'none';
  const genLabel = isHuddle ? '⚡ Generate Huddle Summary' : '⚡ Generate Summary';
  bar.innerHTML = `
    <button class="t-btn primary" id="gen-btn-${{tab.id}}" onclick="generateSummary('${{tab.id}}')">${{genLabel}}</button>
    ${{!isAdhoc ? `<button class="t-btn save" onclick="saveTx('${{tab.id}}')">${{saveLabel}}</button>` : ''}}
    <span class="t-spacer"></span>
    <span class="tx-char-count" id="tx-count-${{tab.id}}">0 chars</span>
    <button class="t-btn danger"  onclick="clearTx('${{tab.id}}')">Clear</button>
  `;
  txPanelsEl.appendChild(bar);

  // Ops log viewer — Huddle tab only
  if (isHuddle) {{
    const logViewer = document.createElement('div');
    logViewer.id    = 'ops-log-viewer';
    logViewer.className = 'ops-log-viewer';
    logViewer.style.display = 'none';
    const entries = DATA.ops_log || [];
    if (entries.length === 0) {{
      logViewer.innerHTML = '<div class="ops-log-viewer-header">Ops Log — no entries yet</div>';
    }} else {{
      const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      let html = `<div class="ops-log-viewer-header">📋 Ops Log — ${{entries.length}} entries</div>`;
      entries.forEach((entry, i) => {{
        html += `<div class="ops-log-entry" id="ops-entry-${{i}}">
          <div class="ops-log-entry-title" onclick="toggleOpsEntry(${{i}})">
            <span class="ops-log-entry-chevron">▶</span>
            <span>${{esc(entry.title)}}</span>
          </div>
          <div class="ops-log-entry-body">
            <div class="ops-log-entry-body-inner">${{esc(entry.body)}}</div>
          </div>
        </div>`;
      }});
      logViewer.innerHTML = html;
    }}
    txPanelsEl.appendChild(logViewer);
  }}
}});

function toggleOpsEntry(i) {{
  const el = document.getElementById('ops-entry-' + i);
  if (el) el.classList.toggle('open');
}}

function switchTab(tabId) {{
  repTabsEl.querySelectorAll('.rep-tab-btn').forEach(b => b.classList.remove('active'));
  txPanelsEl.querySelectorAll('.transcript-content').forEach(p => p.style.display = 'none');
  txPanelsEl.querySelectorAll('.transcript-action-bar').forEach(b => b.style.display = 'none');
  repTabsEl.querySelector(`[data-tab-id="${{tabId}}"]`).classList.add('active');
  document.getElementById('tx-panel-' + tabId).style.display = 'grid';
  document.getElementById('tx-bar-'  + tabId).style.display = 'flex';
  // Show ops log viewer only on Huddle tab
  const olv = document.getElementById('ops-log-viewer');
  if (olv) olv.style.display = tabId === 'huddle' ? 'block' : 'none';
}}

function onTxInput(tabId) {{
  const val = document.getElementById('tx-input-' + tabId).value;
  if (!txState[tabId]) txState[tabId] = {{}};
  txState[tabId].transcript = val;
  saveTxState();
  document.getElementById('tx-count-' + tabId).textContent = val.length + ' chars';
}}

function onTxOutput(tabId) {{
  const val = document.getElementById('tx-output-' + tabId).value;
  if (!txState[tabId]) txState[tabId] = {{}};
  txState[tabId].output = val;
  saveTxState();
}}

function setNameWarning(tabId, msg) {{
  const el = document.getElementById('tx-warning-' + tabId);
  if (!el) return;
  if (msg) {{
    el.textContent = msg;
    el.style.display = 'block';
  }} else {{
    el.textContent = '';
    el.style.display = 'none';
  }}
}}

async function generateSummary(tabId) {{
  const transcript = document.getElementById('tx-input-' + tabId).value.trim();
  const tab = ALL_TABS.find(t => t.id === tabId);
  if (!transcript) {{ showToast('Paste a transcript first'); return; }}

  const btn      = document.getElementById('gen-btn-' + tabId);
  const outEl    = document.getElementById('tx-output-' + tabId);
  const isHuddle = tab && tab.type === 'huddle';
  const isAdhoc  = tab && tab.type === 'adhoc';

  // Clear any previous warning
  setNameWarning(tabId, null);

  btn.disabled = true;
  btn.textContent = '⏳ Generating…';
  outEl.value = '';
  outEl.placeholder = 'Generating — this takes 20–40 seconds…';

  try {{
    const res = await fetch('http://localhost:5678/api/summarize', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        repId:      tab ? tab.id   : tabId,
        repName:    tab ? tab.name : tabId,
        transcript: transcript,
        isHuddle:   isHuddle,
        isAdhoc:    isAdhoc
      }})
    }});
    const data = await res.json();
    if (data.ok) {{
      outEl.value = data.summary;
      if (!txState[tabId]) txState[tabId] = {{}};
      txState[tabId].output = data.summary;
      saveTxState();
      if (data.name_warning) {{
        setNameWarning(tabId,
          `⚠️ Name mismatch — "${{tab ? tab.name : tabId}}" was not found in the transcript. `
          + `Save to log will write to ${{tab ? tab.name : tabId}}'s file. `
          + `Switch to the correct tab before saving.`);
        showToast('⚠️ Name mismatch — check the warning above before saving', 4000);
      }} else {{
        showToast('✅ Summary ready — save to log or copy as Slack message', 3000);
      }}
    }} else {{
      outEl.placeholder = 'Generated summary will appear here...';
      showToast('⚠️ ' + (data.error || 'Generation failed'), 4000);
    }}
  }} catch(e) {{
    outEl.placeholder = 'Generated summary will appear here...';
    showToast('⚠️ Server offline — run dashboard/server.py', 4000);
  }}

  btn.disabled = false;
  btn.textContent = isHuddle ? '⚡ Generate Huddle Summary' : '⚡ Generate Summary';

}}

function copySlackMessage(tabId) {{
  const output = document.getElementById('tx-output-' + tabId).value.trim();
  if (!output) {{ showToast('Paste the summary output first'); return; }}
  copyToClipboard(output, 'Slack message copied — paste into Slack');
}}

// Routes save to the right endpoint based on tab type
function saveTx(tabId) {{
  const tab = ALL_TABS.find(t => t.id === tabId);
  if (tab && tab.type === 'huddle') saveToOpsLog(tabId);
  else saveToLog(tabId);
}}

async function saveToLog(repId) {{
  // Block save if name mismatch warning is showing
  const warnEl = document.getElementById('tx-warning-' + repId);
  if (warnEl && warnEl.style.display !== 'none' && warnEl.textContent) {{
    showToast('⚠️ Fix the name mismatch before saving', 3000);
    return;
  }}
  const summary = document.getElementById('tx-output-' + repId).value.trim();
  if (!summary) {{ showToast('Generate a summary first'); return; }}
  try {{
    const res  = await fetch('http://localhost:5678/api/save-log', {{
      method:  'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body:    JSON.stringify({{ repId, summary }})
    }});
    const data = await res.json();
    if (data.ok) {{
      showToast('💾 Saved to log — dashboard refreshing…', 3000);
      clearTx(repId);
      // Reload page after brief delay so regenerated HTML loads
      setTimeout(() => location.reload(), 2500);
    }} else {{
      showToast('⚠️ ' + (data.error || 'Save failed'));
    }}
  }} catch (e) {{
    showToast('⚠️ Server offline — run dashboard/server.py');
  }}
}}

async function saveToOpsLog(tabId) {{
  const summary = document.getElementById('tx-output-' + tabId).value.trim();
  if (!summary) {{ showToast('Paste the /teamreview output first'); return; }}
  try {{
    const res  = await fetch('http://localhost:5678/api/save-ops-log', {{
      method:  'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body:    JSON.stringify({{ summary, label: 'Huddle' }})
    }});
    const data = await res.json();
    if (data.ok) {{
      showToast('💾 Saved to ops-log — dashboard refreshing…', 3000);
      clearTx(tabId);
      setTimeout(() => location.reload(), 2500);
    }} else {{
      showToast('⚠️ ' + (data.error || 'Save failed'));
    }}
  }} catch (e) {{
    showToast('⚠️ Server offline — run dashboard/server.py');
  }}
}}

function clearTx(tabId) {{
  document.getElementById('tx-input-'  + tabId).value = '';
  document.getElementById('tx-output-' + tabId).value = '';
  document.getElementById('tx-count-'  + tabId).textContent = '0 chars';
  if (txState[tabId]) delete txState[tabId];
  saveTxState();
  showToast('Cleared');
}}

// Restore char counts from saved state on load
ALL_TABS.forEach(tab => {{
  const tx      = document.getElementById('tx-input-' + tab.id);
  const countEl = document.getElementById('tx-count-' + tab.id);
  if (tx && countEl) countEl.textContent = tx.value.length + ' chars';
}});

// ── Voice Input ─────────────────────────────────────────────────────────────
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

function startVoice(tabId) {{
  if (!SpeechRec) {{ showToast('🎤 Voice not supported — use Chrome or Safari'); return; }}
  const btn = document.getElementById('voice-btn-' + tabId);
  const ta  = document.getElementById('tx-input-'  + tabId);

  // Toggle off if already recording
  if (btn.classList.contains('recording')) {{
    if (btn._rec) btn._rec.stop();
    return;
  }}

  const rec = new SpeechRec();
  rec.continuous     = true;
  rec.interimResults = true;
  rec.lang           = 'en-US';

  // Start from current textarea content
  let baseText = ta.value;
  if (baseText) baseText = baseText.trimEnd() + ' ';

  rec.onresult = e => {{
    let interim = '', final = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {{
      if (e.results[i].isFinal) final += e.results[i][0].transcript + ' ';
      else interim += e.results[i][0].transcript;
    }}
    if (final) baseText += final;
    ta.value = baseText + interim;
    onTxInput(tabId);
    ta.scrollTop = ta.scrollHeight;
  }};

  rec.onerror = e => {{
    showToast('🎤 ' + (e.error === 'not-allowed' ? 'Mic permission denied' : 'Error: ' + e.error));
    btn.classList.remove('recording');
    btn.textContent = '🎤 Voice';
    btn._rec = null;
  }};

  rec.onend = () => {{
    btn.classList.remove('recording');
    btn.textContent = '🎤 Voice';
    btn._rec = null;
  }};

  rec.start();
  btn._rec = rec;
  btn.classList.add('recording');
  btn.textContent = '⏹ Stop';
  showToast('🎤 Listening… click Stop when done');
}}

// ── Auto-refresh: poll /api/version every 30s, reload when HTML changes ──────
let _lastVersion = null;
async function checkVersion() {{
  // Don't reload if user is actively typing in any textarea
  const active = document.activeElement;
  if (active && active.tagName === 'TEXTAREA') return;
  try {{
    const r = await fetch('http://localhost:5678/api/version', {{cache: 'no-store'}});
    if (!r.ok) return;
    const {{v}} = await r.json();
    if (_lastVersion === null) {{ _lastVersion = v; return; }}
    if (v !== _lastVersion) {{
      _lastVersion = v;
      showToast('📡 Dashboard updated — reloading…', 1500);
      setTimeout(() => window.location.reload(), 1600);
    }}
  }} catch(e) {{ /* server offline — ignore */ }}
}}
setInterval(checkVersion, 30000);
checkVersion();
</script>

</body>
</html>"""

# ── Backup helpers ─────────────────────────────────────────────────────────────
def _backup(src: Path, backup_dir: Path, prefix: str, keep: int = 20):
    """Copy src into backup_dir with a timestamp suffix, pruning old copies."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = backup_dir / f"{prefix}_{ts}{src.suffix}"
    shutil.copy2(src, dest)
    # Prune oldest beyond keep limit
    copies = sorted(backup_dir.glob(f"{prefix}_*{src.suffix}"))
    for old in copies[:-keep]:
        old.unlink()
    return dest


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    data = build_data()
    html = generate_html(data)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    BACKUP_DIR = OUTPUT_FILE.parent / "backups"

    # Backup generate.py itself (the source of truth)
    _backup(Path(__file__), BACKUP_DIR / "generate", "generate", keep=20)

    # Backup the outgoing index.html before overwriting
    if OUTPUT_FILE.exists():
        _backup(OUTPUT_FILE, BACKUP_DIR / "html", "index", keep=20)

    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"✓ Dashboard generated → {OUTPUT_FILE}")
    print(f"  Revenue:  ${data['progress'].get('TOPTAL_REVENUE', 0):,} / ${data['progress'].get('TOPTAL_TARGET', 624270):,} ({data['revenue_pct']}%)")
    print(f"  1:1s:     {data['one_on_ones']}  |  Open actions: {data['open_actions']}")
    print(f"  Team:     {', '.join(r['name'] + '(' + r['signal'][0].upper() + ')' for r in data['team'])}")
    if "--open" in sys.argv:
        subprocess.run(["open", str(OUTPUT_FILE)])
