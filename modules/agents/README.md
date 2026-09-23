# Agent configuration

This module owns portable shared instructions, personal skills, and the Claude
Code status line. Edit the sources here; the installer exposes them under
`~/.agents/` and the application entry points.

## Layout and discovery

```text
modules/agents/
  AGENTS.md                 shared user instructions
  skills/<name>/SKILL.md     portable skill sources and supporting files
  install.conf.yaml          Dotbot links
  status-line.sh             Claude-specific status line

~/.agents/AGENTS.md          -> this module's AGENTS.md
~/.agents/skills/<name>      -> this module's skills/<name>
~/.codex/AGENTS.md           -> this module's AGENTS.md
~/.claude/CLAUDE.md          -> this module's AGENTS.md
~/.claude/skills/<name>      -> this module's skills/<name>
```

Codex discovers user skills in `~/.agents/skills` and project skills in
`.agents/skills` along its project ancestry. It still uses its native global
instruction entry point. Do not also link the same skills in `~/.codex/skills`.
Claude uses `.claude/skills`; it does not discover the neutral directory itself.
Bundled skills, including Codex's `hatch-pet`, and plugin caches remain owned
by each application and are excluded from this module.

The normal `./install` applies this module for roles that include `agents`.
To reapply only this module without changing the saved role selection, run
from the repository root:

```sh
dotbot/bin/dotbot -d "$PWD/modules/agents" -c modules/agents/install.conf.yaml --plugin-dir lib/dotbot-plugins
```

## Project convention

Keep shared authored context under `<project>/.agents/`. A project's root
`AGENTS.md` and `CLAUDE.md` point to `.agents/AGENTS.md`. Claude Code reads
`AGENTS.md` when a directory has no `CLAUDE.md`, so a project with only a
root `AGENTS.md` (such as a vault from `modules/obsidian`) needs no
`CLAUDE.md`; its Claude skills still go in `.claude/skills/`. A distinct Claude
instruction document can live at `.agents/CLAUDE.md` with its existing entry
point retained. Nested instruction scopes use the same layout in that scope.
Project skill sources live at `.agents/skills/<name>`; Claude gets individual
relative links from `.claude/skills/<name>`. Codex reads the neutral path.

The notes vault keeps its visible `AGENTS.md` documents authoritative so they
remain readable in Obsidian on the phone. Its `.agents/AGENTS.md` links back to
the visible file, and `CLAUDE.md` imports it. Never link in both directions.
Projects without existing authored context do not need empty scaffolding.

Native settings, MCP registrations, credentials, permissions, plugins,
generated plans, and automatic memories stay in the owning application's
directories. Shared authored context is not a merge of native memory stores.

## Local integrations

Machine-local overrides and rules may live in `~/.agents/` with links from
the native application paths. They are outside this public repository.
The portable `vault` skill is a lightweight entry point installed from this
module. It selects the vault and follows its `AGENTS.md` and relevant references.
Each vault owns its capture destinations and workflows. The former daily-journal
skill and global daily adapters are retired. Private references stay local.
This installer has no required dependency on those files or on a notes vault.

## Skill provenance

`vault` replaces the former local `homebase` user skill. Its general vault
workflow lives here; application-specific Homebase procedures belong to that
application's project skills. The old global `homebase` links are retired.
