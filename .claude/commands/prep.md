# /prep — Meeting Prep Orchestrator

Prepares a meeting deck end-to-end. Drafts narrative commentary, writes it directly into the Google Slides presentation, and queues a Slack ping on completion.

## Usage

```
/prep huddle
/prep catalyst
/prep dan
```

---

## Catalyst — Rules & Workflow

**Timing**: Bi-weekly. Only run on prep week. Ops adds fresh slides to the deck — always wait for them before writing. The newest "Michael V." slides are the current session's set.

**Target slides**: Always find the slides with **"Michael V."** in the text — these are the EMEA section. The slide numbers shift each session as new slides are prepended by ops.

**Never overwrite**: The "Today's Topics + Key Inputs" text block — leave it exactly as ops set it.

**Write to** (on Michael V. slides only):
- `Task Management` box — what we committed last session, what got done, what slipped
- `Top Opportunities` box — top open opportunities and key context from rep logs

**Data sources:**

Tableau (requires michael.veltman@toptal.com signed into Tableau in browser):
- Revenue/Actuals: `https://10az.online.tableau.com/t/toptal/views/SMBRevenueTargets/ActualsVsTargets/`
- Activity metrics: `https://10az.online.tableau.com/t/toptal/views/Sandbox-SMBSalesActivityMetrics/InboundMetrics/`
- Gong scorecard: `https://10az.online.tableau.com/t/toptal/views/SandboxNewScorecard-PerformanceInitiative/GongCallDetails/1cd30f31-e26c-4b67-98b2-205e07b94b04/269049b1-8702-4f30-bc3a-f43a60a87c98`
- Funnel conversion: `https://10az.online.tableau.com/t/toptal/views/WIPSMB-ConversionRateMockup/ConversionRatesHQTrends/03203f7b-3c07-4936-80ed-826584e03a07/d5d8ba4c-9894-4d49-bd2e-7e9b374920da`

Staff Portal (requires Toptal SSO session in browser):
- Job Station (EMEA team, last 30 days, non-marketplace): `https://staff.toptal.com/job_station?cumulative_statuses%5B%5D=pending_engineer&cumulative_statuses%5B%5D=pending_claim&cumulative_statuses%5B%5D=pending_legal&cumulative_statuses%5B%5D=pending_start&cumulative_statuses%5B%5D=on_trial&cumulative_statuses%5B%5D=on_hold&posted_at=last_30_days&team_ids%5B%5D=120041&marketplace=false&page=1`

Job Station — expected data format to extract and include in Top Opportunities commentary:
```
Pending Talent
  Total: [n]       Avg/rep: [n]
  On Trial: [n]    Pending Start: [n]    End Scheduled: [n]
```

**Activity metrics output format** — show in command centre BEFORE writing to deck:
```
Catalyst Prep — Activity Metrics
Please peruse and let me know what you think. I'll only paste into the deck when you give me the green light.

QTD Lead Funnel — SMB
Period: [start date] → [end date]

Snapshot (WoW)
• Claimed Leads: [prev] → [curr] ([+/-%])
• FSC: [prev] → [curr] ([+/-%])
• Approved: [prev] → [curr] ([+/-%])
• Verified: [prev] → [curr] ([+/-%])
• Posted Jobs: [prev] → [curr] ([+/-%])
• Engagement Starts: [prev] → [curr] ([+/-%])
• WES: [prev] → [curr]

Signal: [1-sentence read of what the data says — front-end / mid-funnel / activation]

Focus Areas
1. [Metric] — Direction: [+/-% WoW]
   Why it matters: [1-2 sentences on business impact]
2. [Metric] — Direction: [+/-% WoW]
   Why it matters: [1-2 sentences on business impact]

QTD Direction
[2-3 sentence arc: spike/dip pattern, current position, what it signals going forward]

Decision
[1 clear action sentence — what to maintain, watch, or change]

Numbers Only Appendix (QTD)
Week | Date | Claimed | FSC | Approved | Verified | Posted | Eng | WES | Active | Ended
[full weekly table]
```

**'High Priority Cadence' Task Completion**: Skip for now — data not yet accessible.

**Screenshots via Tableau/Staff Portal** (navigate → screenshot → present to Michael for manual paste):
- Gong scorecard: Gong scorecard URL → screenshot heatmap filtered to EMEA → for "Gong Call Scoring & Call Quality" slide
- Funnel conversion: Funnel conversion URL → screenshot → for "Funnel Conversion" slide
- Job Station: navigate to Job Station URL → screenshot or read Pending Talent numbers → use in Top Opportunities text commentary (numbers only, no screenshot needed)

**Manual only** (cannot be automated at all):
- Revenue attainment chart (data chart — ops/Tableau, requires Tableau embed)

---

## What It Does

### Step 0 — Account verification (ALWAYS run first)
Before doing anything, surface which accounts are active:

**Google Slides auth check:**
```bash
TOKEN=$(python3 -c "import json; print(json.load(open('/Users/michaelveltman/My second brain/dashboard/token.json'))['token'])")
curl -s "https://www.googleapis.com/drive/v3/about?fields=user&access_token=$TOKEN"
```
- ✅ `michael.veltman@toptal.com` → proceed
- ⚠️  `michaeljveltman@gmail.com` → STOP. Tell Michael: "Google Slides is authenticated as your personal Gmail, not Toptal. Run `python3 slides_updater.py --auth` to re-authenticate as michael.veltman@toptal.com before continuing."

**Tableau session check:**
- Navigate to Activity Metrics URL
- If it lands on Tableau SSO login → flag: "Tableau not signed in — sign in as michael.veltman@toptal.com then let me know"
- If dashboard loads → proceed

**Staff Portal (Job Station) session check:**
- Navigate to Job Station URL
- If it lands on toptal.com/users/login → flag: "Staff Portal not signed in — click 'Log in with Google' using michael.veltman@toptal.com"
- If Job Station loads → proceed

Always output a status block before continuing:
```
🔐 Account Check
   Google Slides : michael.veltman@toptal.com ✅
   Tableau       : signed in ✅
   Staff Portal  : signed in ✅
```
Hard stop on any ⚠️ — do not proceed until all three are Toptal.

### Step 1 — Load context
- Read the Catalyst deck via `slides_updater.py --read catalyst`
- Find all slides containing "Michael V." — these are the current EMEA section
- Read each rep's `team/*/log.md` for signals, recent commitments, and themes from last 2 weeks
- Read `progress.md` for any updated revenue/attainment figures
- Navigate to Tableau Actuals vs Targets and read EMEA revenue figures

### Step 2 — Draft commentary
For **Catalyst** (bi-weekly):
- **Task Management**: What was committed at last session (from rep logs + ops-log.md), what got done, what slipped, what carries forward
- **Top Opportunities**: 3–5 top open deals or engagements across the team with brief status notes
- Revenue attainment narrative: QTD actual vs target, % attainment, direction of travel vs 13-week trend

### Step 3 — Preview before writing
Show a preview of drafted commentary per text box and ask:
"Ready to write this to the slides? I'll update [deck name] now → [confirm / edit]"

Wait for confirmation before proceeding.

### Step 4 — Write to slides (with confirmation)
⚠️ NEVER use `--keyword` for writes — "Task Management" and "Top Opportunities" appear on multiple manager slides. Always use `--object-id` with the ID found during Step 1 `--read`.

At the start of each session, capture the Michael V. object IDs from the `--read` output:
```bash
# Step 1: find the IDs
python3 ".../slides_updater.py" --read catalyst
# Identify the object_id on the Michael V. slide 18 (Task Management) and slide 21 (Top Opportunities)
# Then write using those IDs:

python3 "/Users/michaelveltman/My second brain/dashboard/slides_updater.py" \
  --update catalyst --object-id "<task_mgmt_obj_id>" --text "<drafted text>"

python3 "/Users/michaelveltman/My second brain/dashboard/slides_updater.py" \
  --update catalyst --object-id "<top_opps_obj_id>" --text "<drafted text>"
```

### Step 5 — Slack ping (with explicit permission)
After slides are updated, ask:
"Ping the channel to announce the deck is ready? (yes/no)"

If yes, compose the message and ask for send confirmation before posting.

---

## Huddle — Rules & Workflow

**Timing**: Weekly.

**Write to**: Commentary boxes on Michael's slides. Drafts 2–3 bullets per slide.
- Revenue trend slide: YTD revenue, gap to target, week-on-week movement
- Revenue vs Target: % attainment, tone (on track / behind / at risk)
- Record Board: Jobs Posted trend and what it signals for pipeline health

---

## Dan 1:1 — Rules & Workflow

**Timing**: Bi-weekly.

**Write to**: Commentary boxes on Michael's slides.
- Revenue snapshot: QTD target, attainment %, what's driving it
- Funnel health: 13-week lens, where reps are strong vs needing support
- Action items / asks for Dan

---

## Notes
- Only write to text elements — never data charts or screenshot placeholders
- Always use `--keyword` to find elements rather than hardcoding object IDs (slide positions shift)
- If `credentials.json` or `token.json` is missing: `python3 slides_updater.py --setup-help`

## Prerequisites
- `credentials.json` and `token.json` in `dashboard/` directory
- Authenticated as michael.veltman@toptal.com (run `python3 slides_updater.py --auth` if needed)
