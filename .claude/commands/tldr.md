# /tldr — Session Summary + Weekly Digest

## When to use
Type `/tldr` at the end of any Claude Code session to capture what happened. Type `/tldr week` to force a weekly digest on any day.

---

## Step 1: Check the day and time

Run:
```
date '+%A %Y-%m-%d %H:%M'
```
This gives: day-name YYYY-MM-DD HH:MM (local machine time, Europe/Dublin). Save all three values — you need the day name, date, and time for later steps.

If the day name is `Friday`, produce both the session summary (Steps 2–4) AND the weekly digest (Step 5) automatically.

If the user typed `/tldr week`, produce the weekly digest (Step 5) regardless of day.

Otherwise, produce only the session summary (Steps 2–4).

---

## Step 2: Create sessions/ folder if needed

```
mkdir -p sessions
```

The filename for the session file uses HHMM (no colon) for filesystem compatibility. The frontmatter `time:` field uses HH:MM (with colon). This asymmetry is intentional.

---

## Step 3: Write the session file

Path: `sessions/YYYY-MM-DD-HHMM.md` (use values from Step 1)

Reflect on this conversation and write:

```
---
date: YYYY-MM-DD
time: HH:MM
type: session
---
# Session — DD Month YYYY · HH:MM

## Decisions made
- [What was decided — not what was discussed]

## Things built or changed
- [Files created or modified, features added, configs changed]

## Open items
- [Anything unfinished or to pick up next session]

## Files touched
- [List of file paths changed in this session]
```

Keep each section to 3–5 bullets. Signal only — not a transcript. Write `- None` for empty sections rather than omitting them.

---

## Step 4: Write the ops-log entry

Read `team/ops-log.md`. Prepend the following block immediately after the `<!-- OPS LOG ENTRIES — newest at top -->` marker:

```
---
## YYYY-MM-DD | Michael | Session Summary

[1-2 sentences: what was worked on and the key outcome]

➡️ [Open item 1 — only if there are open items]
➡️ [Open item 2 — only if there are open items]

---
```

Rules:
- Label is always `Michael`, type is always `Session Summary`
- Use `➡️` for open items only — omit those lines entirely if none exist
- The 1-2 sentence summary should match what you wrote in Step 3

---

## Step 5: Weekly digest (Fridays + `/tldr week`)

Only run this step if today is Friday OR the user typed `/tldr week`.

Get this week's Monday:
```
date -v-mon +%Y-%m-%d
```

Note: on a Monday, this returns today's date — that is correct behaviour (the week started today). The session file search range will be narrow (today only) which is expected.

Find this week's session files: Use Glob to find all files matching `sessions/YYYY-MM-DD-*.md`. Read the `date:` frontmatter from each. Keep only files whose date falls between the Monday date (inclusive) and today (inclusive).

Edge case — fewer than 2 distinct calendar dates found: If fewer than 2 different dates appear among the found files, also include session files from the previous Friday (the Friday before the Monday date). In that case, add this line at the top of the digest body: `(includes carry-over from previous week)`

Write the weekly digest at path: `sessions/week-of-YYYY-MM-DD.md` (YYYY-MM-DD = the Monday date):

```
---
date: YYYY-MM-DD
type: weekly-digest
---
# Week of DD Month YYYY

## Key decisions this week
- ...

## Things built or shipped
- ...

## Recurring themes
- [Patterns appearing across multiple sessions]

## Open items carried forward
- [Consolidated open items from all session files this week]
```

---

## Done

Tell the user:
- Session saved to `sessions/YYYY-MM-DD-HHMM.md`
- Ops log updated in `team/ops-log.md`
- (If applicable) Weekly digest saved to `sessions/week-of-YYYY-MM-DD.md`
