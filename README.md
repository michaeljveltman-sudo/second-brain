# Second Brain — A Command Centre Built on Claude Code

## What this is

A second brain that builds itself while you work. Instead of a static note-taking system, this one uses Claude Code slash commands to capture, summarise, and surface your work automatically. It comes with a live browser dashboard that pulls from your notes in real time — one example: after a team huddle, type `/huddlesummary` and get a Slack-ready summary in under 30 seconds.

## What's included

- Slash commands: `/log`, `/tldr`, `/ingest`, `/1on1`, `/huddlesummary`, and others
- A live browser dashboard (your Command Centre) that auto-generates from your notes
- Templates and frameworks in `brain/` for proposals, discovery calls, meeting notes, and more
- A team management system with per-rep context files and a shared ops log

## What you need

- [Claude Code](https://claude.ai/code)
- 10 minutes

## Setup in 4 steps

1. Download this repo (click the green "Code" button → "Download ZIP")
2. Open the folder in Claude Code
3. Edit `CLAUDE.md` to describe yourself — your role, your team, your goals
4. Type `/dashboard` to see your Command Centre

## The 5 commands you'll use daily

| Command | What it does |
|---|---|
| `/log [name]` | Record a coaching session or 1:1 note |
| `/tldr` | End-of-session summary — saves to file and ops log automatically |
| `/ingest [file or URL]` | Drop any document into your vault as clean markdown |
| `/1on1 [name]` | Prep for a 1:1 before it happens |
| `/huddlesummary` | Turn a team huddle transcript into a Slack-ready summary |

## How to make it yours

The only required change is editing `CLAUDE.md`. That file tells Claude who you are — your role, your team, the context it needs to be useful. Everything else adapts automatically from there.

Want to add your own commands? Create a plain `.md` file in `.claude/commands/` and it becomes a slash command. No code required.

## Questions / issues

Find me on [LinkedIn](https://www.linkedin.com/in/michael-v-499990134/).
