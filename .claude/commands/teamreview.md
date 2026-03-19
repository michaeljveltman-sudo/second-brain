# /teamreview — Weekly Team Review

## Trigger
User types: `/teamreview` or `/teamreview [week of date]`

## Purpose
Pull the latest from all 6 rep logs + ops-log and produce a structured weekly team picture.
Used for: Monday planning, leadership updates, identifying who needs attention this week.

---

## What to Do

### Step 1: Load all rep context and recent logs
For each rep in `/team/`:
- Read their `context.md` (profile, current coaching focus)
- Read last 2-3 entries from their `log.md`

Also read `/team/ops-log.md` — last 5 entries for recent patterns.

### Step 2: Build the Weekly Team Review

---

## Output Format

```
# Weekly Team Review — [Week of Date]
Target: $624,270 | Team: 6 reps

---

## 🔴 Needs Attention This Week
[Reps with risk signals, stuck deals, missed commitments, or patterns that need direct coaching]

- [Rep name]: [1-2 lines — what's happening and what action Michael should take]
- [Rep name]: ...

---

## 🟡 Watch Closely
[Reps who are fine but have something worth monitoring]

- [Rep name]: [What to watch and why]

---

## ✅ Performing Well
[Reps with positive signals — wins, momentum, good coaching responses]

- [Rep name]: [What's working]

---

## 🔁 Team-Wide Patterns This Week
[Themes appearing across multiple reps — these are coaching, process, or lead quality issues]

- [Pattern]: [Which reps, what's happening, recommended response]

---

## 🎯 Coaching Priority This Week
[The ONE coaching focus for the team this week — based on the pattern above]

**Focus**: [Specific skill or behaviour]
**Why now**: [What the logs are showing]
**How to address**: [In team meeting / individual 1:1 / Crash Course topic / Gong call review]

---

## ➡️ Michael's Action Items This Week
[Concrete things Michael needs to do, not the team]

1. [Action — who, what, by when]
2. [Action]
3. [Action]

---

## 📊 Pipeline Snapshot (from log data)
[Based on notes in the logs — this is from what's been logged, not live HubSpot]

| Rep | Pipeline Signal | Last Activity Noted | Watch-out |
|-----|----------------|--------------------| ---------|
| [Name] | [Strong/OK/Thin] | [Date] | [If any] |
...

---

## 💬 Suggested Team Meeting Agenda
Based on this week's patterns:
1. [Topic — e.g. "Handling the decision process question earlier in discovery"]
2. [Topic — e.g. "Review the [Rep]'s deal that closed — what worked?"]
3. [Topic — e.g. "Pipeline hygiene — next steps with dates"]

```

---

## After the Review
Ask: "Want me to draft the team meeting agenda, prep a 1:1 for any of these reps, or log anything from this week?"
