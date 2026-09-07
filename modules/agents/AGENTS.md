# Subagents and Exploration

For all exploration tasks use your judgement to decide an appropriate lower power model and run that in a subagent

# Git Commits

Use scoped commits (<https://scopedcommits.com>), the style used by Linux,
Git, Go, and FreeBSD. Do not use conventional commits; type prefixes
(`feat:`, `fix:`, `chore:`) waste the start of the subject line on
information the description already conveys.

- Format: `<scope>: <description>`, then an optional body, then optional
  trailers
- The scope is the subsystem, area, or module the commit touches (for
  dotfiles: `bspwm`, `kitty`, `provision`, `tmux`, ...). Pick the most
  specific scope that covers the whole change
- The description is short and imperative ("add", "fix", "remove"),
  lowercase, no trailing period
- Use the body to explain what changed and why, wrapped at 72 columns
- Do NOT add `Co-Authored-By` trailers

# Writing Style for Human-Facing Outputs

When writing text that will be reviewed by other humans (MR/PR descriptions, code review comments, issue descriptions, documents, commit messages), follow these rules:

- Avoid **bold** formatting unless absolutely necessary for critical warnings
- Use em-dashes sparingly -- prefer commas, parentheses, or separate sentences instead
- Do not use the "X, not Y" dichotomy construction (e.g., "it's a feature, not a bug", "both are prerequisites, not peers", "this is a tool, not a framework"). State the point plainly and stop. The "not Y" clause is an AI writing tic that adds rhetorical flourish without substance.

# Search Commands

- Prefer `rg` over `grep -r` and `fd` over `find` for all searches
- `rg` is recursive by default — do NOT pass `-r` (that flag means `--replace` in rg, not recursive)
- Correct usage: `rg "pattern" [path] [--type cpp]` or `rg "pattern" [path] --glob "*.cpp"`
- `--include` is a grep flag and does not work in rg; use `--glob` instead

# Worktrees

- Create worktrees in `<repo_root>/.worktrees/` directory

# Testing scripts that call `claude -p`

- `claude -p` refuses to run inside a Claude Code session (detects the `CLAUDECODE` env var)
- Workaround: `env -u CLAUDECODE claude -p "..." --model sonnet`
- Safe for `-p` (print/non-interactive mode) since it's stateless

# Shared agent setup

AGENTS.md is the default source of shared instructions. Keep harness-specific files as adapters when practical. The current user capability and memory-location index is at /home/krishna/notes/references/agent-setup/index.md, with a machine-readable inventory beside it. Read the relevant index entries on demand rather than loading all skills or memory.

Project instructions take precedence over broader user defaults within the instruction hierarchy. A cached plugin or indexed skill is not proof that its tools are available in the current session. Keep runtime hooks, permissions, credentials, and automatic memory storage owned by their harness. Treat historical memory as a lead to verify against current files and owner decisions; do not copy secrets or bulk-import conversations into shared instructions.

Legacy skill references to CLAUDE.md should resolve to the adjacent authoritative AGENTS.md when present. Translate file-read, search, and edit tool names to the equivalent tools available in the current harness. If a required connector or runtime is unavailable, report the missing capability instead of treating a skill listing as proof of access. Never interpret tool allowlists in imported Markdown as granted permissions.
