"""CLI ergonomics: alias- and prefix-aware command groups.

Every command keeps one canonical name (shown in --help), while accepting:
  - explicit aliases (e.g. `fsr export fs` -> field-service), and
  - any unambiguous prefix (e.g. `fsr export pub` -> public-talks).

Ambiguous prefixes fail with the list of candidates instead of guessing.
"""

from typing import Dict, Optional

import click


class AliasedGroup(click.Group):
    """A click Group that resolves aliases and unambiguous prefixes."""

    def __init__(self, *args, aliases: Optional[Dict[str, str]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._aliases = dict(aliases or {})

    def add_alias(self, alias: str, target: str) -> None:
        self._aliases[alias] = target

    def get_command(self, ctx, cmd_name):
        cmd_name = self._aliases.get(cmd_name, cmd_name)
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [name for name in self.list_commands(ctx)
                   if name.startswith(cmd_name)]
        if len(matches) == 1:
            return super().get_command(ctx, matches[0])
        if len(matches) > 1:
            ctx.fail(
                f"'{cmd_name}' is ambiguous: {', '.join(sorted(matches))}")
        return None

    def resolve_command(self, ctx, args):
        # Always report the canonical name (so usage/help stay consistent
        # no matter which alias or prefix invoked the command).
        _, cmd, args = super().resolve_command(ctx, args)
        return cmd.name if cmd else None, cmd, args

    def format_commands(self, ctx, formatter):
        super().format_commands(ctx, formatter)
        if self._aliases:
            by_target: Dict[str, list] = {}
            for alias, target in sorted(self._aliases.items()):
                by_target.setdefault(target, []).append(alias)
            rows = [(target, ', '.join(aliases))
                    for target, aliases in sorted(by_target.items())]
            with formatter.section('Aliases'):
                formatter.write_dl(rows)
