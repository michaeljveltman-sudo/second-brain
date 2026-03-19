# /ingest — Document Pipeline

## When to use
Drop any document into your vault as clean, compressed markdown.
- `/ingest path/to/file.pdf` — local PDF
- `/ingest path/to/file.docx` — local Word doc
- `/ingest https://docs.google.com/...` — Google Drive document
- `/ingest https://drive.google.com/...` — Google Drive file
- `/ingest` — interactive mode (prompts for input)

---

## Step 1: Determine the input

If an argument was provided after `/ingest`: apply the same type detection as rules 3–6 below to determine which sub-step of Step 2 to use, then go there directly (skip the interactive prompt).

If no argument (interactive mode): Respond to the user: "Paste the content, a file path, or a URL — then press Enter twice. Type 'cancel' to exit."

When the user responds, detect the input type in this exact order:
1. Empty input → stop silently
2. Exactly `cancel` (case-insensitive) → respond "Cancelled." and stop
3. Starts with `https://docs.google.com` or `https://drive.google.com` → Google Drive URL → go to Step 2c
4. Starts with `http://` or `https://` (any other domain) → respond: "I can't fetch that URL directly — paste the content and I'll process it." Then re-prompt: show the interactive mode prompt again and run input detection on the next input.
5. Starts with `/`, `~`, or `.` AND ends with a file extension → local file path → go to Step 2a or 2b based on extension
6. Anything else → pasted text → go to Step 2d

---

## Step 2: Extract the content

### 2a — Local PDF

First try pdftotext:
```
pdftotext "FILE_PATH" -
```

If that command fails (not installed), try PyPDF2/pypdf:
```
python3 -c "
try:
    import PyPDF2 as pdf_lib
    reader = pdf_lib.PdfReader('FILE_PATH')
except ImportError:
    import pypdf as pdf_lib
    reader = pdf_lib.PdfReader('FILE_PATH')
print('\n'.join(p.extract_text() or '' for p in reader.pages))
"
```

If both fail, tell the user: "PDF extraction failed. Run `brew install poppler` in Terminal, then try again. Or paste the text directly."

### 2b — Local .docx
```
python3 -c "
import docx
doc = docx.Document('FILE_PATH')
print('\n'.join(p.text for p in doc.paragraphs if p.text.strip()))
"
```

If the command fails (e.g. `python-docx` not installed), tell the user: "Word doc extraction failed. Run `pip3 install python-docx` in Terminal, then try again. Or paste the text directly."

### 2c — Google Drive URL

Use the `google_drive_fetch` MCP tool with the full URL. Valid patterns include:
- `https://docs.google.com/document/d/...`
- `https://docs.google.com/spreadsheets/d/...`
- `https://drive.google.com/file/d/...`
- Any of the above with `?usp=sharing`

### 2d — Pasted text

Use the input directly — no extraction needed.

---

## Step 3: Compress to signal

Take the extracted text and write clean, compressed markdown:
- Remove boilerplate: headers/footers, page numbers, legal disclaimers, navigation menus, repeated section titles
- Keep: key facts, decisions, requirements, names, dates, numbers
- Target: a 20-page document → 1–2 pages of signal

---

## Step 4: Determine the destination

Classify the content:

| Content type | Destination |
|---|---|
| Client brief, project doc, job spec | `clients/[client-name]/context.md` |
| Prospect or lead information | `prospects/[prospect-name]/context.md` |
| Research, frameworks, teaching material | `brain/knowledge/[topic].md` |
| Side Quest / AI × Sales content | `sidehustle/content/[topic].md` |

If the content clearly matches one category: go to Step 5.

If ambiguous or matching multiple categories equally: pick your best guess and confirm with the user: "This looks like [X] — file under [path]? Or choose: clients / prospects / brain / sidehustle / other." Always recommend one option — never present a tie without a preference.

If the user chooses "other": ask for the full destination path ("Where should I file this? Give me a path like `notes/topic.md`."), then use that path in Step 5.

---

## Step 5: Check for an existing file

Use Glob to check if the destination file exists.

**File does NOT exist:** create it (the Write tool creates parent directories automatically — no mkdir needed). Go to Step 6.

**File DOES exist:** Read the first 5 lines and show the user:
"A file already exists at [path]:
[first 5 lines]
Append new content, overwrite, or save as [path]-YYYY-MM-DD.md?"

Wait for their choice. If they don't specify in the same message, default to saving as a new dated file — never silently overwrite.

---

## Step 6: Write the output file

Get today's date:
```
date +%Y-%m-%d
```

Write the file with this frontmatter and content:
```
---
source: [original filename or URL]
ingested: YYYY-MM-DD
type: [client-brief / research / teaching / prospect / etc]
---
# [Inferred title from content]

[Compressed content — signal only]
```

---

## Done

Tell the user:
- What was ingested (source name or URL)
- Where it was filed (full path)
- Approximate output size (e.g. "compressed to 42 lines")

---
