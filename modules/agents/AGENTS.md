# Git Commits

Use scoped commits (<https://scopedcommits.com>), the style used by Linux, Git, Go, and FreeBSD. Do not use conventional commits; type prefixes (`feat:`, `fix:`, `chore:`) waste the start of the subject line on information the description already conveys.

- Format: `<scope>: <description>`, then an optional body, then optional trailers
- The scope is the subsystem, area, or module the commit touches (for
  dotfiles: `bspwm`, `kitty`, `provision`, `tmux`, ...). Pick the most specific scope that covers the whole change
- The description is short and imperative ("add", "fix", "remove"), lowercase, no trailing period
- Use the body to explain what changed and why, wrapped at 72 columns
- Do NOT add `Co-Authored-By` trailers

# Worktrees

- Create worktrees in `<repo_root>/.worktrees/` directory

# Local instructions

Read @~/.claude/AGENTS.local.md
