---
name: optimize
user-invocable: true
disable-model-invocation: false
description: >
  Vault-wide audit and housekeeping. Triggers on: "optimize vault", "audit",
  "housekeeping", "check vault", "vault health", "vault audit",
  "optimize notes", "clean up vault"
allowed-tools: Read, Glob, Grep, Write(~/notes/*), Edit, Bash(ls *)
---

# Optimize

Vault-wide audit and housekeeping. Checks structural conventions, frontmatter completeness, and content staleness.

## Arguments

Optional `[scope]`: `all`, `projects`, `concepts`, `references`, `daily`. Default: `all`.

## Procedure

### 1. Load all vault conventions

Read CLAUDE.md files:
- `~/notes/CLAUDE.md` (vault root)
- `~/notes/concepts/CLAUDE.md`
- `~/notes/projects/CLAUDE.md`
- `~/notes/projects/courses/CLAUDE.md`
- `~/notes/references/CLAUDE.md`
- `~/notes/daily/CLAUDE.md`
- `~/notes/templates/CLAUDE.md`

### 2. Structural audit

- Every project subfolder has an `index.md` with `aliases: [folder-name]` in frontmatter
- Files are in the correct directory for their `type` frontmatter value
- No orphan files in vault root (outside of known top-level files)
- Wikilinks in index files resolve to existing notes

### 3. Frontmatter audit

Check required fields per type:
- Project files: `type`, `status`, `description`, `tags`
- Concept files: `status`, `tags`
- Reference files: `type`, `tags`
- Daily notes: `date`
- Valid status values: `active`, `paused`, `backlog`, `complete`, `ongoing` (projects); `seedling`, `budding`, `evergreen` (concepts)

### 4. Staleness audit

Using frontmatter `created` date:
- Seedling concepts >60 days old with <100 chars content (beyond frontmatter)
- Active projects >90 days old with only stub content
- Empty files (<50 chars beyond frontmatter)
- Missing `created` field: flag as frontmatter issue
- Never flag `evergreen` or `complete` status as stale

### 5. Report

- Summary count: "Found N issues: X critical, Y warnings, Z info"
- Severity-grouped table (critical first)
- Cap at 20 issues per run
- Severity guide:
  - Critical: missing index.md, wrong directory for type, broken required frontmatter
  - Warning: missing optional frontmatter, stale content, orphan files
  - Info: concept extraction candidates, minor inconsistencies

### 6. Execute approved fixes

User approves by category or individually:
- Missing indices: create from template with proper frontmatter
- Missing frontmatter fields: add with sensible defaults
- Misplaced files: suggest move, confirm before executing
- Never modify note content (only metadata and structure)

### 7. Report changes

- Files created, modified, or moved
- Issues resolved vs remaining
