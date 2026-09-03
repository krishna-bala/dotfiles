"""render - a dotbot directive for the few files that differ per machine.

Symlinks carry everything in this repo except a handful of values that are
genuinely per-host (a panel's DPI, redshift's location, a wifi interface
name). Those files are templates: ``${NAME}`` placeholders substituted from
the generated ``$XDG_CONFIG_HOME/dotfiles/host.env`` (written by ./install
from hosts/defaults.env, hosts/<hostname>.env, and the untracked
dotfiles/local.env), and the result is *copied* to its destination.

    - render:
        ~/.Xresources: Xresources.tmpl
        ~/.config/redshift.conf:
          path: redshift.conf.tmpl
          mode: "0644"

Sources are relative to dotbot's base directory (the module), like ``link``.
A placeholder with no value is an error, not a blank - a silently empty DPI
is worse than a failed install. Rendering is idempotent: an unchanged
destination is left untouched and reported as such.
"""

import os
import string
from typing import Any

import dotbot

HOST_ENV_VAR = "DOTFILES_HOST_ENV"


def _load_env(path: str) -> dict:
    values: dict = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


class Render(dotbot.Plugin):
    _directive = "render"

    def can_handle(self, directive: str) -> bool:
        return directive == self._directive

    def handle(self, directive: str, data: Any) -> bool:
        if directive != self._directive:
            raise ValueError(f"Render cannot handle directive {directive}")
        env_path = os.environ.get(HOST_ENV_VAR) or os.path.join(
            os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"),
            "dotfiles",
            "host.env",
        )
        if not os.path.isfile(env_path):
            self._log.error(f"render: host env file not found: {env_path} (run ./install)")
            return False
        env = _load_env(env_path)

        base = self._context.base_directory()
        ok = True
        for dest, spec in data.items():
            if isinstance(spec, dict):
                source = spec["path"]
                mode = int(spec.get("mode", "0644"), 8)
            else:
                source = spec
                mode = 0o644
            ok = self._render_one(base, source, dest, mode, env) and ok
        if ok:
            self._log.info("All templates rendered")
        else:
            self._log.error("Some templates could not be rendered")
        return ok

    def _render_one(self, base: str, source: str, dest: str, mode: int, env: dict) -> bool:
        src_path = os.path.join(base, source)
        dest_path = os.path.abspath(os.path.expanduser(dest))
        try:
            with open(src_path, encoding="utf-8") as fh:
                template = fh.read()
        except OSError as exc:
            self._log.error(f"render: cannot read {src_path}: {exc}")
            return False
        try:
            rendered = string.Template(template).substitute(env)
        except KeyError as exc:
            self._log.error(f"render: {source} needs {exc.args[0]}, which host.env does not define")
            return False
        except ValueError as exc:
            self._log.error(f"render: {source}: {exc}")
            return False

        # A destination that is a symlink (an earlier install linked the
        # untemplated file) must be replaced, never written through.
        if os.path.islink(dest_path):
            os.unlink(dest_path)
        elif os.path.isfile(dest_path):
            with open(dest_path, encoding="utf-8") as fh:
                if fh.read() == rendered and (os.stat(dest_path).st_mode & 0o777) == mode:
                    self._log.lowinfo(f"Up to date {dest}")
                    return True

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        tmp_path = dest_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as fh:
            fh.write(rendered)
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, dest_path)
        self._log.lowinfo(f"Rendered {dest} <- {source}")
        return True
