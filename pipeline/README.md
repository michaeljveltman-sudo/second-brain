# Pipeline Folder

## Purpose
Active deal tracking. One file per deal. Used by the Pipeline Manager agent and the `/pipeline` command.

## File Naming
`[company-name]-[YYYY-MM].md`
Example: `acme-corp-2026-03.md`

## How to Use
1. Create a new file for each active deal
2. Use the prospect context template as a starting point
3. Update after every conversation
4. Run `/pipeline` weekly to get AI analysis and prioritization

## Fields That Matter Most for AI Analysis
- Current stage
- MEDDPICC score
- Next step WITH a date
- Last activity date
- Deal value

## Monthly Archive
Move closed (won/lost) deals to `/pipeline/archive/[year-month]/` at month end.
Document loss reasons — this becomes your coaching data.
