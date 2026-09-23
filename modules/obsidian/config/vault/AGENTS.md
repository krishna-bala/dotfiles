# Work vault

Local work knowledge vault. Start navigation at [[Home]].

## Local only

- This vault lives only on this machine. It is not synced anywhere (no Obsidian Sync, no cloud folder, no sync plugins).
- Git is for local history only. The repo has no remote; never add one, push, or copy notes to an outside service.
- Do not paste vault content into external tools, issues, or chats unless the owner asks for that specific content to go there.
- `.obsidian/` settings are committed here because nothing leaves the machine. `workspace*.json`, `.env*`, and local agent settings are ignored.

## Structure

```
concepts/          # Ideas you synthesized: flat, evergreen, reusable
projects/          # Things you work on: features, investigations, incidents, recurring meetings
references/        # External information: people, teams, systems, processes
  people/
archive/           # Finished or historical material
templates/         # Templater templates
attachments/       # Pasted images and files
_inbox/            # Default location for new notes; sort regularly
.claude/           # Claude Code skills, hooks, and settings for this vault
```

- Boundary test: "Did I author this insight?" → `concepts/`. "Am I recording external info?" → `references/`. "Am I working on it?" → `projects/`.
- Folders describe domain, not status. Completed projects stay in `projects/` with `status: complete`.
- Meetings live with the project they belong to (`projects/<project>/meetings/`), or under `projects/meetings/` for recurring ones with no single project.
- Add an `AGENTS.md` to a folder when it gains conventions of its own. This file is authoritative at the root; folder files add local rules.

## Properties (frontmatter)

- Universal: `type`, `created`, `tags`.
- `type` values: `project`, `meeting`, `person`, `design-note`, `concept`, `reference`, `index`.
- Projects: `status` (`active`, `paused`, `backlog`, `complete`, `ongoing`), `timeframe`, `team`.
- Meetings: `attendees`, optionally `recurring`, `schedule`.
- People: `team`, `role`, `aliases`.
- Index files serve as MOCs with dataview queries and include `aliases: [<folder-name>]` so they can be linked as `[[folder-name]]`.

## Writing conventions

- Write each prose paragraph on a single source line and let Obsidian wrap it. Preserve Markdown structure for lists, tables, code blocks, and headings.
- No H1 headings; the filename is the title.
- Links: `[[Entity]]` for wikilinks, `[[Note#Section]]` for sections, `[text]` in single brackets for visual distinction only (ticket numbers, tool names), `#tag` for categories and states.
- Callouts: `> [!definition]`, `> [!theorem]`, `> [!example]`, `> [!note]`. Formal callout first, informal explanation after.
- Math: `$...$` inline, `$$...$$` display. Use `\mathbf{x}` (not `\bold`), and bold only the variable name.
- Distinguish decisions, proposals, and open questions. Record who decided and when.

## Templates

Templater templates in `templates/`: `meeting`, `project`, `person`, `design-note`. Insert with `Alt+O`, or create a note from a template with `Alt+Mod+O`. Use `<% tp.date.now("YYYY-MM-DD") %>` for dates.

## Vim mode

Vim bindings come from the Vimrc Support plugin and `.obsidian.vimrc` at the vault root (LazyVim-style: `jk`/`jj` escape, `<Space><Space>` quick switcher, `<Space>:` command palette, `<C-h/j/k/l>` split navigation, `gd` follow link).

## Agents

AGENTS.md is the instruction file at every scope. Put Claude Code specific skills, hooks, and settings under `.claude/` (`.claude/skills/<name>/SKILL.md`, `.claude/settings.json`); `.claude/settings.local.json` and `.claude/plans/` stay untracked.
