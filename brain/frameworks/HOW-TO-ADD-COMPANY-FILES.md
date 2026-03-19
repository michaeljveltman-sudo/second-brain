# How to Add Internal Company Files

## Before Adding Anything — Quick NDA Check
Ask yourself: "Would I be comfortable if a colleague saw this file here?"
- General process docs, frameworks, onboarding materials → fine
- Confidential client data, commercial terms, internal financials → don't add
- Your own notes and observations about how things work → fine

---

## What to Add and Where

### /brain/frameworks/ — Process and methodology docs
Good candidates:
- Sales playbook / process documentation
- Qualification criteria or ICP definitions
- Onboarding framework for new reps
- Coaching frameworks or templates
- KPI definitions and how they're measured
- Commercial model overview (Subscription, Marketplace)

### /brain/knowledge/ — Reference and context
Good candidates:
- Product/service overview docs
- Competitive positioning notes
- Common client industry briefs
- Frequently asked questions and answers
- Training materials you've created

### /clients/ — Client memory (you create these manually)
One folder per client. Use the template in `/clients/_template/`.

### /pipeline/ — Active deals (you create these manually)
One file per active deal.

---

## File Formats That Work Best
- **Markdown (.md)** — best. Claude reads these perfectly.
- **Plain text (.txt)** — also great.
- **PDF** — readable but slower. Convert to .md if you can.
- **.docx** — needs conversion. Run: `python3 -c "import docx; doc=docx.Document('file.docx'); print('\n'.join([p.text for p in doc.paragraphs]))" > output.md`

---

## How the AI Uses These Files
Once a file is in the right folder, any command that loads that folder's context will have access to it.
Example: Drop a sales playbook into `/brain/frameworks/sales-playbook.md` and it will automatically inform the `/discovery`, `/proposal`, and `/pipeline` commands.

No extra setup needed. The file just needs to be there.

---

## Recommended First Files to Add
1. **Your team's current sales playbook** (or your version of it) → `/brain/frameworks/`
2. **KPI definitions** (what metrics matter, how they're calculated) → `/brain/knowledge/`
3. **Your onboarding framework** for new reps → `/brain/frameworks/`
4. **Common objections specific to your market context** → add to `/brain/frameworks/objection-handling.md`
5. **Your coaching template or 1:1 framework** → `/brain/templates/`
