# /summary — Draft Slack-Ready 1:1 Summary from Transcript

## Trigger
User types: `/summary [rep name] — [paste transcript or notes here]`

Examples:
- `/summary Annmarie — [Gong/Zoom transcript]`
- `/summary Emilio — [raw notes from today's call]`
- `/summary Mike Lyon — [paste of Slack messages / call notes]`

---

## What to Do

### Step 1: Identify the rep
- Match the name to a folder in `/team/`
- If rep not found — flag it and ask for clarification

### Step 2: Load rep context
- Read `/team/[rep-name]/context.md` — communication style, coaching focus, themes, current signal
- Read the last 2-3 entries in `/team/[rep-name]/log.md` — what was discussed recently, open commitments
- This context ensures the summary is grounded in patterns, not just today's call

### Step 3: Read + interpret the transcript
From the raw transcript or notes, extract:
- **Discussion themes**: what was actually talked about (not just what was said)
- **Coaching moments**: what skill or behaviour came up and what was the message
- **Action items**: what the rep committed to (with clear outcomes)
- **Manager observations**: Michael's read on the session — what stood out, what to watch, what was good

### Step 4: Write the Slack-Ready Summary

**This must be copy-paste ready — no editing required.**

Use EXACTLY this format. No deviations:

```
:notebook: 1:1 Notes – [Rep Name] – [Date]

:memo: Discussion Summary

• [Point 1 — what was discussed, what it means]
• [Point 2]
• [Point 3]
• [Point 4]
• [Point 5 — 4 to 6 bullets max]

:white_check_mark: Action Items for [Rep Name]

:one: [Action] → [why this matters / outcome it drives]
:two: [Action] → [why this matters / outcome it drives]
:three: [Action] → [why this matters / outcome it drives]

:thought_balloon: Michael's Comments
• [Observation or coaching note]
• [Second observation — encouragement, risk, or next step]
• [Third if needed — specific thing to watch or revisit next session]
```

**Format rules (non-negotiable)**:
- :notebook: opens the summary — always
- :memo: Discussion Summary — 4 to 6 bullets only
- :white_check_mark: Action Items — numbered with :one: :two: :three: emoji (not 1. 2. 3.)
- :thought_balloon: Michael's Comments — 2 to 4 bullets; honest, direct, human
- No blockquotes, no tables, no headers inside the blocks
- Bullets use • not - or *
- Tone: confident and direct, not corporate. Michael's voice — coaching, not managing.
- The "→ why it matters" in action items is mandatory — these aren't just tasks, they're development moves

### Step 5: Produce the Chat-Thread Timeline Entry

After the Slack summary, produce a shorter internal log entry for the rep's thread log:

```
[Date] — [Week/session context e.g. "Pipeline review" or "Career development session"]

Context: [1 sentence — what prompted this session or what stage they're at]

Key Points:
• [Point 1]
• [Point 2]
• [Point 3]

Ongoing Items:
• 🆕 [New item] → [Owner], [Due date if stated]
• 🔄 [Ongoing item] → [Owner], [Status]
• ✅ [Closed item] → [Owner], Closed [date]

📊 Status Check
Performance: [Strong / Progressing / Below target]
Focus: [High / Medium / Low]
Confidence: [High / Medium / Low — based on how they showed up in the session]
Support Needed: [What they actually need right now]
```

### Step 6: Offer to log it
After producing the summary, ask:
"Want me to log this to [rep name]'s file now? I'll also update the ops-log. Just say `/log` and I'll handle it."

---

## Quality Check (apply before outputting)

Before producing the final summary, verify:
- [ ] Discussion bullets are insights, not just event summaries ("discussed X" is not enough — what was the meaning?)
- [ ] Action items have a clear outcome/rationale after the →
- [ ] Manager's comments sound like Michael — direct, honest, a bit irreverent if appropriate, not corporate
- [ ] The format exactly matches the template — no deviations
- [ ] The summary would make sense to someone who wasn't on the call
- [ ] Open commitments from last session are referenced if relevant

---

## Guardrails

- Always use ICF coaching frameworks as background context when interpreting what happened:
  - What was the coachee's energy / level of engagement?
  - What was the coaching action (ask, reframe, challenge, support)?
  - What were the observable commitments?
- The Slack summary is for Annmarie/Emilio/etc. to see — it should be professional and motivating
- The Manager's Comments section is also visible to the rep — write honestly but not harshly
- If the transcript is thin or unclear, flag what's missing and ask: "I don't have enough on [X] — what happened there?"

---

## Example Output

:notebook: 1:1 Notes – Tanya – 19 Aug 2025

:memo: Discussion Summary

• Tanya is working on interpreting dashboards and wants personalised systems for better data analysis
• Michael stressed storytelling with data and using ROA prep to link metrics clearly
• AI tools like Gemini and Gong can boost funnel analysis, pitch prep, and note-taking efficiency
• Client expectations shaped by AI need careful handling to maintain trust
• They agreed objection-handling cheat sheets would help address AI concerns

:white_check_mark: Action Items for Tanya

:one: Use a more data-driven approach in ROA presentations → builds confidence with clear, evidence-backed storytelling
:two: Practice dashboard analysis bi-weekly → sharpens Tanya's skills and reduces reliance on Michael's coaching over time
:three: Draft objection-handling notes for AI-related concerns → ensures Tanya is ready for client pushback and sets realistic expectations

:thought_balloon: Michael's Comments
• Strong initiative from Tanya in wanting to personalise her dashboard approach
• Focus on linking data to a story clients can follow, not just numbers
• Let's review progress on objection-handling notes next week
