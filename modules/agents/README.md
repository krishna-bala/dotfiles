# Shared agent configuration

AGENTS.md is shared through the Claude and Codex user instruction links. Vault-specific instructions and the capability catalog live in ~/notes/references/agent-setup/index.md. Four existing file-based skills are exposed through ~/.agents/skills; plugins, credentials, native memory, and hooks remain harness-owned.

Run python3 modules/agents/configure-codex.py from this checkout to enable CLAUDE.md fallback in an existing Codex config. AGENTS.md remains primary. The updater preserves unrelated parsed settings. Do not run an obsolete backup repository's installer. Skill links in install.conf.yaml refer to the current XPS marketplace checkout.
