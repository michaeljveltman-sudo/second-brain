# /log — Add Entry to Rep Log + Ops Log

## Trigger
User types: `/log [rep name] — [notes from 1:1 / observation / coaching moment]`

Examples:
- `/log Sarah — 1:1 today. Pipeline thin, 2 deals stuck in eval for 3 weeks. Coached on urgency framing.`
- `/log James — strong call this morning, used the "what did you ask it?" reframe naturally. First time without prompting.`
- `/log all — team meeting. Common theme: reps not asking about decision process early enough.`

---

## What to Do

### Step 1: Identify the rep
- Match the name to a folder in `/team/`
- If "all" — this is a team-wide observation, goes to ops-log only
- If rep not found — flag it and ask for clarification

### Step 2: Read the rep's context
- Load `/team/[rep-name]/context.md` for background on this person
- Load last 3 entries from `/team/[rep-name]/log.md` for recent history

### Step 3: Process the notes
From what Michael shared, extract:
- **Entry type**: 1:1 / call observation / pipeline review / ad hoc / team-wide
- **Key facts**: what happened, what was discussed
- **Coaching moment** (if any): what was the skill/behaviour and what was the coaching action
- **Commitments**: what did the rep commit to? What did Michael commit to?
- **Performance signal**: positive / negative / neutral
- **Pattern**: does this connect to anything from recent entries?

### Step 4: Write the rep log entry

Format — append to TOP of `/team/[rep-name]/log.md` after the `<!-- ENTRIES BELOW -->` comment:

```
---
## [Date] — [Entry type: 1:1 / Call review / Pipeline review / Ad hoc]

**Summary**: [1-2 sentences — what happened]

**Detail**:
- [Key point 1]
- [Key point 2]
- [Key point 3 if needed]

**Coaching**: [What was coached, how it was framed, how they responded]

**Commitments**:
- Rep: [What they committed to] — by [date if mentioned]
- Michael: [What Michael committed to] — by [date if mentioned]

**Signal**: [🟢 Positive / 🟡 Watch / 🔴 Risk] — [1-line reason]

**Pattern note**: [Does this connect to previous entries? Note it.]

---
```

### Step 5: Write the ops log entry

Format — append to TOP of `/team/ops-log.md` after the `<!-- OPS LOG ENTRIES -->` comment:

```
---
## [Date] | [Rep Name] | [Entry type]

[1-2 sentence summary of what happened and why it matters at a team level]

[Flag if relevant: ✅ win / 🔴 risk / 🔁 pattern / 🎯 coaching decision / ➡️ action for Michael]

---
```

### Step 6: Surface patterns (if any)

After writing both entries, check:
- Is this issue appearing in multiple reps? Flag it.
- Is there a trend in this rep's recent entries?
- Does Michael need to take any action based on this?

Output a brief summary: "Logged. [1 sentence on what was filed]. [Pattern note if relevant]."

---

## Edge Cases

**If notes are thin** (e.g. `/log Sarah — quick check in, all good`):
- Write a minimal entry, flag that it's light on detail
- Ask: "Anything specific to note on pipeline or coaching focus?"

**If it's a performance concern**:
- Make the signal 🔴 in both logs
- Add: "➡️ Consider: is this a coaching issue or a fit issue?"

**If it's a strong win**:
- Make the signal ✅
- Add: "➡️ Share with team? Could be a teaching moment."
