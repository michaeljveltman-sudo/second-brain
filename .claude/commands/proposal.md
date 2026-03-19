# /proposal — Generate a Client Proposal

## Trigger
User types: `/proposal for [Client/Prospect] focusing on [topic/need]`

## What to Do

1. **Load client context** — Read `/clients/[client-name]/context.md` or `/prospects/[name]/context.md` if it exists
2. **Load proposal template** — Read `/brain/templates/proposal-template.md`
3. **Load proposal structure framework** — Read `/brain/frameworks/proposal-structure.md`
4. **Load quality standards** — Read `/brain/frameworks/quality-standards.md`

## Build the Proposal

Structure:
1. **Executive Summary** (3-4 sentences max — why this, why now, why Toptal/Michael)
2. **Understanding of Their Challenge** (show you've listened — their specific pain)
3. **Proposed Solution** (specific Toptal talent profile OR teaching engagement details)
4. **Why Toptal / Why Michael** (2-3 proof points, relevant to their industry)
5. **Engagement Model** (timeline, deliverables, next steps)
6. **Investment** (pricing — use `/brain/frameworks/pricing.md` if exists)
7. **Next Steps** (single clear CTA)

## Quality Check
Before outputting, validate:
- [ ] Executive summary is < 4 sentences
- [ ] No fluff words (leverage, synergy, ecosystem, game-changer)
- [ ] Client's specific pain is mentioned by name
- [ ] Clear single next step
- [ ] Tone matches: professional but human

## Output Format
Output the full proposal, then ask: "Want me to adjust the tone, pricing section, or any specific section?"
