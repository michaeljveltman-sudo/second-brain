# /dashboard — Refresh and Open Command Centre

## Trigger
User types: `/dashboard` or `/dashboard refresh`

---

## What to Do

### Step 1: Regenerate the dashboard HTML
Execute:
```
python3 "/Users/michaelveltman/My second brain/dashboard/generate.py"
```

### Step 2: Report the output
Show the terminal output (revenue, 1:1s, team signals), then say:
"Dashboard regenerated. Open it at http://localhost:5678 — or start the server with:
`python3 '/Users/michaelveltman/My second brain/dashboard/server.py'`"

---

## Notes
- **Full dashboard with save-to-log**: run `server.py` which serves the dashboard at `http://localhost:5678` and enables the 💾 Save to log / Save to ops-log buttons in the Transcript Inbox
- **Quick preview only**: `generate.py --open` opens the file directly via `file://` — transcript save buttons will show "Server offline" toast
- The dashboard reads live from `progress.md` and all rep `log.md` files
- Run after `/progress update` to see updated bars
- Sidebar command buttons copy to clipboard on click
- Transcript Inbox: paste a 1:1 or huddle transcript → copy the `/summary` or `/teamreview` command → paste into Claude → paste result back → 💾 save directly to the rep's log or ops-log
