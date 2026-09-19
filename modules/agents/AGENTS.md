# Subagents and Exploration

For all exploration tasks use your judgement to decide an appropriate lower power model and run that in a subagent

# Git Commits

Use scoped commits (<https://scopedcommits.com>), the style used by Linux, Git, Go, and FreeBSD. Do not use conventional commits; type prefixes (`feat:`, `fix:`, `chore:`) waste the start of the subject line on information the description already conveys.

- Format: `<scope>: <description>`, then an optional body, then optional trailers
- The scope is the subsystem, area, or module the commit touches (for
  dotfiles: `bspwm`, `kitty`, `provision`, `tmux`, ...). Pick the most specific scope that covers the whole change
- The description is short and imperative ("add", "fix", "remove"), lowercase, no trailing period
- Use the body to explain what changed and why, wrapped at 72 columns
- Do NOT add `Co-Authored-By` trailers

# Writing Style for Human-Facing Outputs

When writing text that will be reviewed by other humans (MR/PR descriptions, code review comments, issue descriptions, documents, commit messages), follow these rules:

- Avoid **bold** formatting unless absolutely necessary for critical warnings
- Use em-dashes sparingly -- prefer commas, parentheses, or separate sentences instead
- Do not use the "X, not Y" dichotomy construction (e.g., "it's a feature, not a bug", "both are prerequisites, not peers", "this is a tool, not a framework"). State the point plainly and stop. The "not Y" clause is an AI writing tic that adds rhetorical flourish without substance.

# Worktrees

- Create worktrees in `<repo_root>/.worktrees/` directory
