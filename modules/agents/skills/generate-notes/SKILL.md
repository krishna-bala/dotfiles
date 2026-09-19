---
name: generate-notes
user-invocable: true
disable-model-invocation: false
description: >
  Creates vault notes from a source. Triggers on: "generate notes", "take notes on",
  "create notes from", "summarize this into notes", "notes from this URL",
  "notes from this paper", "notes from this chapter"
allowed-tools: WebFetch, Read, Write(~/notes/*), Bash(curl *), Bash(mkdir *), Glob, Grep
---

# Generate Notes

Creates structured vault notes from a source (URL, file, folder, or pasted text). No Anki interaction.

## Arguments

`<src>` is a URL, file path, folder path, or the user pastes text directly.

## Procedure

### 1. Load conventions

- Read `~/notes/CLAUDE.md` for vault-wide conventions (LaTeX, linking, callouts, frontmatter)
- If the target directory is known, read its CLAUDE.md too (e.g., `~/notes/projects/courses/underactuated/CLAUDE.md`)

### 2. Acquire source content

- URL: `WebFetch(url, "Extract key concepts, definitions, equations in LaTeX, and section structure")`. If WebFetch fails, ask user to paste content.
- File/PDF: `Read(path)` (for PDFs, use `pages` parameter for large ones)
- Folder: `Glob` for files, then `Read` each
- Pasted text: use directly

### 3. Triage large sources

If source is large (>10k words estimated):
- Summarize the structure and sections found
- Ask user which sections to prioritize
- Process in priority order

### 4. Determine target location

If not obvious from context:
- Analyze source type (course chapter? standalone concept? reference?)
- Ask user where notes should live
- Suggest based on vault structure conventions

### 5. Extract images (URL sources only)

- Fetch raw HTML: `Bash(curl -s <url>)`
- `Grep` for image URLs (`src="...svg|jpg|png"`)
- Download relevant images: `Bash(curl -s -o ~/notes/<target>/figures/<filename> <image_url>)`
- Create figures directory if needed: `Bash(mkdir -p ~/notes/<target>/figures/)`
- If extraction fails, continue without images and note the gap

### 6. Create notes

Write note(s) at the appropriate vault path with:
- Proper frontmatter per directory CLAUDE.md conventions
- LaTeX using `$...$` and `$$...$$` (vault format, NOT Anki format)
- `\mathbf{x}` for bold (NOT `\bold{x}`)
- Embedded figures: `![[figures/filename.svg]]`
- Wikilinks to existing concepts where applicable
- Callout blocks for formal definitions, theorems, examples per vault conventions

### 7. Report

- Note path(s) created
- Sections covered
- Images stored (if any)
- Suggest running `/generate-cards` if the notes contain card-worthy material
