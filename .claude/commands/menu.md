# /menu — Command Launcher

## Trigger
User types: `/menu` | `/menu toptal` | `/menu sidehustle`

---

## What to Do

### Step 1: Read progress data
- Read `/Users/michaelveltman/My second brain/progress.md`
- Extract these values from the HTML comment keys:
  - `TOPTAL_REVENUE`, `TOPTAL_TARGET`, `TOPTAL_WEEK`, `TOPTAL_1ON1S_DONE`, `TOPTAL_1ON1S_TOTAL`, `TOPTAL_OPEN_ACTIONS`
  - `SH_POSTS_PUBLISHED`, `SH_POSTS_DRAFTED`, `SH_TRACK1_PCT`, `SH_TRACK2_PCT`, `SH_STATUS`
- Calculate: `REVENUE_PCT = round((TOPTAL_REVENUE / TOPTAL_TARGET) * 100)`

### Step 2: Determine display mode
- `/menu` — render BOTH blocks (Toptal + Side Quest)
- `/menu toptal` — render Toptal block only
- `/menu sidehustle` — render Side Quest block only

### Step 3: Render the menu

Use EXACTLY this format. Substitute live values from progress.md.

---

**For Toptal block:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢  TOPTAL  ·  Wk[TOPTAL_WEEK]  ·  Q1 [REVENUE_PCT]%  ·  ⚡ [TOPTAL_OPEN_ACTIONS] open
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  TEAM MANAGEMENT
  ─────────────────────────────────────────────────
  /1on1 [name]     → Prep for a rep 1:1
  /summary [name]  → Slack-ready summary from transcript
  /log [name]      → Log a session or coaching note
  /teamreview      → Weekly team review across all reps

  PIPELINE & DEALS
  ─────────────────────────────────────────────────
  /pipeline        → Review and prioritise current pipeline
  /discovery [co]  → Prep a discovery call briefing
  /followup [co]   → Write a post-call follow-up email
  /proposal [co]   → Build a client proposal

  DOCUMENTS
  ─────────────────────────────────────────────────
  /email           → Draft an email in your voice
  /brief           → Create a project or engagement brief
```

**For Side Quest block:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀  SIDE QUEST  ·  [SH_STATUS]  ·  Track 1: [SH_TRACK1_PCT]%  ·  Track 2: [SH_TRACK2_PCT]%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  CONTENT
  ─────────────────────────────────────────────────
  /linkedin        → Draft a LinkedIn post
  /lesson [topic]  → Build teaching content (Track 1 or 2)
  /email           → Draft an email or outreach in your voice
  /proposal [pkg]  → Build a course or workshop proposal

  Posts: [SH_POSTS_PUBLISHED] published  ·  [SH_POSTS_DRAFTED] drafted
```

**When showing both, put Toptal first, then a blank line, then Side Quest.**

**Bottom footer (always show when rendering both or toptal):**

```

  ─────────────────────────────────────────────────
  /progress        → View full progress bars
  /progress update [field] [value]  → Update any metric
```

### Step 4: Stop
No follow-up question. No "what would you like to do?" — just render the menu and wait.

---

## Notes
- Values that are 0 should display as `0` not blank
- REVENUE_PCT: if revenue is 0, show `0%`; round to nearest whole number
- SH_STATUS: display as-is from the data file (e.g. "building", "live", "launching")
- The menu is a launcher, not a conversation — keep it tight
