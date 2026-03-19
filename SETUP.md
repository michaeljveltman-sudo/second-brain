# Setup Guide

## Before you start

Two things you need before anything else:

1. **Claude Code** — download and install it from https://claude.ai/code
2. **A folder on your computer** to put this project in (Documents, Desktop, wherever makes sense)

That's it. No coding experience needed.

---

## Getting the files

**Step 1.** On the GitHub repo page, click the green **Code** button, then click **Download ZIP**.

**Step 2.** Unzip the downloaded file somewhere you'll find it — Documents or Desktop both work fine.

**Step 3.** Open Claude Code, then use **Open Folder** to open the unzipped folder. Claude Code needs to see the folder, not just individual files inside it.

---

## Editing CLAUDE.md

`CLAUDE.md` is the file that tells Claude who you are and what you're working on. Open it and replace the following five things:

1. **Your name** — find "Michael Veltman" and replace it with yours
2. **Your role and company** — replace the Toptal description with your actual role, team, and what you sell or do
3. **Your team size** — how many people you manage directly, or write "I work solo" if that's the case
4. **Your tools** — update the list to match what you actually use (your CRM, any call recording tools, your calendar)
5. **Your goals** — replace the current goals with what you're trying to accomplish this quarter

This is the only file you **must** edit. Everything else is optional until you need it.

---

## Running the dashboard

Type `/dashboard` in Claude Code and press Enter.

Claude will generate the dashboard and open it in your browser. It reads your notes and logs and shows team status, tasks for the week, and your command launcher.

Refresh it any time by typing `/dashboard` again.

---

## Your first `/tldr`

At the end of any working session, type `/tldr` in Claude Code.

Claude will write a summary of what you worked on, any decisions made, and anything still open. It saves automatically to a `sessions/` folder inside your project.

On Fridays it also writes a weekly digest pulling from the week's sessions.

---

## Your first `/ingest`

Type `/ingest` and paste in any text — a meeting transcript, a report, notes from a call, anything.

Or type `/ingest path/to/file.pdf` with a file path if you have a document you want to add.

Claude compresses it down to signal-only markdown and files it in the right place. It works with PDFs, Word docs, Google Drive links, and pasted text.

---

## Troubleshooting

**"The dashboard won't open"**
Make sure the `/dashboard` command ran without errors in Claude Code. If you see a Python error, check that Python 3 is installed on your computer.

**"Claude can't find my files"**
Make sure you opened the correct folder in Claude Code. The folder should contain `CLAUDE.md` at the top level — if you can see it, you're in the right place.

**"The commands don't work"**
Check that a folder called `.claude/commands/` exists inside your project folder. Folders starting with `.` are hidden by default — you may need to enable "Show hidden files" in your file manager to see it.

**"/ingest can't read my PDF"**
Try pasting the text directly instead. If you need PDF reading to work, you can install the required tool: on a Mac, open Terminal and type `brew install poppler`.

**"The team cards show no data"**
You need at least one log entry before rep data appears. Add one by typing `/log [name]` in Claude Code and following the prompts.

---

If something looks off, that's normal — just ask Claude what went wrong. It will either fix it or tell you exactly what's missing.
