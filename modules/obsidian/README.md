# obsidian

A starter pack for a new Obsidian vault: settings (Catppuccin appearance,
hotkeys, vimrc, CSS snippet, per-plugin settings), a folder layout, a root
`AGENTS.md`, `Home.md`, and a `.gitignore`. After seeding, each vault owns
its copy and is free to drift from this one.

The module is in no role. `./install` and `./provision.sh` skip it; run the
script by hand.

## Seed a vault

```sh
~/.dotfiles/modules/obsidian/seed-vault ~/my-vault
```

The script copies files without overwriting existing ones, creates the
folders, and runs `git init` with no remote. Re-running it only fills in
what is missing.

## Finish in Obsidian

These steps are manual, or for an agent to walk through with the owner.

1. Open the folder as a vault ("Open folder as vault").
2. Settings → Community plugins: turn off Restricted mode, then Browse
   and install each of these by name. The seeded settings are picked up
   on install.

   | Search for     | Plugin id                 |
   |----------------|---------------------------|
   | Templater      | `templater-obsidian`      |
   | Dataview       | `dataview`                |
   | Style Settings | `obsidian-style-settings` |
   | Vimrc Support  | `obsidian-vimrc-support`  |
   | Date Inserter  | `date-inserter`           |
   | Datepicker     | `datepicker`              |
   | Mermaid Tools  | `mermaid-tools`           |
   | TikZJax        | `obsidian-tikzjax`        |

3. Settings → Appearance → Themes → Manage: install Catppuccin.
4. Restart Obsidian so the vimrc and plugins load.

## Fonts

`appearance.json` asks for Google Sans Flex (text and interface) and
Google Sans Code (monospace). Both are OFL-licensed families on Google
Fonts; neither ships with Linux distributions. Without them Obsidian falls
back to its bundled Inter and the system monospace font, so this step is
cosmetic.

To install on Linux, download both families from fonts.google.com, then:

```sh
mkdir -p ~/.local/share/fonts/google-sans
unzip -o '<downloaded zip>' -d ~/.local/share/fonts/google-sans
fc-cache -f
fc-list | grep -i 'google sans'   # both families should be listed
```

Restart Obsidian afterwards.
