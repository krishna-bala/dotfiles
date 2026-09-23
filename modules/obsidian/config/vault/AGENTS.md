# Vault

Obsidian knowledge vault. Start navigation at [[Home]].

## Storage

- The vault is local to this machine. Git records local history; the repo starts with no remote, and adding one is the owner's decision.
- `.obsidian/` settings are committed alongside the notes. `workspace*.json`, `.env*`, and local agent settings are ignored.

## Structure

```
Projects/          # Things you work on, finite or ongoing, with their meetings and logs
Knowledge/         # How things work: systems, people, processes, ideas, lessons
Archive/           # Finished or historical material
Templates/         # Templater templates
_Inbox/            # Default location for new notes; sort regularly
.claude/           # Claude Code skills, hooks, and settings for this vault
```

- Filing test: "Am I working on it?" → `Projects/`. "Is it something I know or want to look up later?" → `Knowledge/`. Group related notes in subfolders (`Knowledge/People/`) as they accumulate.
- Folders describe domain, not status. Completed projects stay in `Projects/` with `status: complete`.
- New notes land in `_Inbox/`. Move a note to its folder once its home is clear; `Home.md` lists what is waiting.
- Add an `AGENTS.md` to a folder when it gains conventions of its own. This file is authoritative at the root; folder files add local rules.

## Properties (frontmatter)

- Universal: `type`, `created` (`YYYY-MM-DD`), `tags`.
- Projects: `type: project`, `status` (`active`, `paused`, `backlog`, `complete`, `ongoing`). `Home.md` lists every note with `type: project` that is not `complete`, regardless of folder.
- Index files serve as MOCs with dataview queries and include `aliases: [<folder-name>]` so they can be linked as `[[folder-name]]`.

## Writing conventions

- Write each prose paragraph on a single source line and let Obsidian wrap it. Preserve Markdown structure for lists, tables, code blocks, and headings.
- No H1 headings; the filename is the title.
- Dates are `YYYY-MM-DD` everywhere.
- Links: `[[Entity]]` for wikilinks, `[[Note#Section]]` for sections, `[text]` in single brackets for visual distinction only (ticket numbers, tool names), `#tag` for categories and states.
- Callouts: use Obsidian's built-in types (`> [!note]`, `> [!example]`, `> [!tip]`, `> [!warning]`, `> [!question]`).
- Math: `$...$` inline, `$$...$$` display. Use `\mathbf{x}` (not `\bold`).
- Distinguish decisions, proposals, and open questions. Record who decided and when.

## Templates

Templater reads `Templates/`. Templates have frontmatter and no H1; use `<% tp.date.now("YYYY-MM-DD") %>` for dates. When an agent creates a note from a template, it writes the expanded values (such as today's date) instead of the `<% %>` tags.

## Keys

- `Ctrl+P` opens the command palette.
- Vim bindings come from the Vimrc Support plugin and `.obsidian.vimrc` at the vault root: `jk`/`jj` escape, `<Space><Space>` quick switcher, `<Space>fg` search in files, `<Space>e` left sidebar, `<C-h/j/k/l>` split navigation, `gd` follow link.

## Agents

Agents read this `AGENTS.md`; no `CLAUDE.md` is needed. Put Claude Code specific skills, hooks, and settings under `.claude/` (`.claude/skills/<name>/SKILL.md`, `.claude/settings.json`); `.claude/settings.local.json` and `.claude/plans/` stay untracked.
