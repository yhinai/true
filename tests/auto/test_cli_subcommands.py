"""Auto-discovered smoke tests for every Typer CLI subcommand.

Runs `cbc <cmd> --help` for each registered subcommand. Catches broken arg
parsing, missing imports, and unregistered commands automatically when a new
subcommand lands — no test file edits needed.
"""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cbc.main import app

runner = CliRunner()


def _discover_subcommands() -> list[str]:
    names: list[str] = []
    for info in app.registered_commands:
        if info.name:
            names.append(info.name)
        elif info.callback is not None:
            names.append(info.callback.__name__.replace("_", "-"))
    return sorted(set(names))


SUBCOMMANDS = _discover_subcommands()


@pytest.mark.parametrize("subcmd", SUBCOMMANDS, ids=SUBCOMMANDS or ["no-subcommands-discovered"])
def test_subcommand_help(subcmd: str) -> None:
    result = runner.invoke(app, [subcmd, "--help"])
    assert result.exit_code == 0, f"`cbc {subcmd} --help` failed:\n{result.output}"
    assert subcmd in result.output or "Usage" in result.output
