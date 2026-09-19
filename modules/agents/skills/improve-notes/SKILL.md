---
name: improve-notes
user-invocable: true
disable-model-invocation: false
description: >
  Improves vault note quality based on feedback or analysis. Triggers on:
  "improve notes", "fix notes", "update notes", "notes need work",
  "refine notes", "clean up notes"
allowed-tools: Read, Write(~/notes/*), Edit, Glob, Grep
---

# Improve Notes

Improves vault note quality based on review feedback, user input, or structural analysis. No Anki interaction.

## Arguments

Optional `[scope]`: note path, topic/course name, or omitted for broad analysis.

## Procedure

### 1. Load conventions

- Read `~/notes/CLAUDE.md` for vault-wide conventions
- Read the target directory CLAUDE.md for structure-specific conventions

### 2. Resolve scope

- Specific note path: read it directly
- Topic/course name: read `~/notes/.claude/deck-map.yaml` to resolve vault path, then `Glob` for notes in that directory
- Omitted: ask user for target, or scan a suggested directory

### 3. Check for flagged issues

- If `anki-review-feedback.md` exists in the resolved directory, check for entries flagged as note-level issues by `/improve-cards`
- These are prioritized (the card was fine, but the source note needs updating)

### 4. Analyze notes

Scan for:
- Outdated or incomplete content (stub sections, TODO markers)
- Broken wikilinks (`Grep` for `[[...]]` patterns, verify targets exist via `Glob`)
- LaTeX issues (`\bold{x}` instead of `\mathbf{x}`, malformed equations)
- Missing or incorrect frontmatter per directory conventions
- Concept extraction candidates (mature subsections that could become standalone concept notes)
- Inconsistency with Anki cards (if feedback file mentions drift between note and card content)

### 5. Present findings

- Prioritized list with note path, issue description, and proposed fix
- Feedback-flagged issues first, then structural issues
- Cap at 20 findings

### 6. Execute approved fixes

User approves by item or category:
- Content fixes: `Edit` for targeted changes, `Write` only for new files (concept extractions)
- Frontmatter fixes: `Edit` to add/correct fields
- Broken links: fix or remove
- Concept extraction: create new note in `concepts/`, add wikilink from source

### 7. Report

- Notes modified
- New concept notes extracted (if any)
- If note changes affect existing Anki cards, suggest running `/generate-cards` to update or `/improve-cards` to fix
