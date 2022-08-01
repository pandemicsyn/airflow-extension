from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import structlog
import typer

from meltano_sdk.extension_base import DescribeFormat
from meltano_sdk.logging import default_logging_config, parse_log_level
from meltano_sdk.process_utils import Invoker

log = structlog.get_logger()

APP_NAME: str = "mecho"

app = typer.Typer(pretty_exceptions_enable=False)


class EchoPlugin:
    def __init__(self):
        self.echo_invoker = Invoker("echo")  # use built-in echo for demo

    def invoke(self, command_name: str | None, *command_args):
        log.debug("invoke", env=os.environ)
        log.info("invoke", command_name=command_name, command_args=command_args)
        if command_name == "trigger_error":
            log.error("triggering a non-0 exit code!")
            raise typer.Exit(code=2)
        elif command_name == "trigger_exception":
            log.warning("triggering an uncaught exception")
            raise Exception("Triggered exception")
        else:
            result = self.echo_invoker.run_stream(command_name, *command_args)
            sys.exit(result.returncode)

    def describe(self, desc_format: DescribeFormat) -> None:
        desc = {"commands": [":splat", "trigger_error", "trigger_exception"]}
        if desc_format == DescribeFormat.text:
            typer.echo("commands:", desc.items())
        elif desc_format == DescribeFormat.json:
            typer.echo(json.dumps(desc, indent=2))
        elif desc_format == DescribeFormat.yaml:
            raise NotImplementedError("YAML output is not supported by this extension")
        else:
            raise ValueError(f"Unknown format: {desc_format}")


plugin = EchoPlugin()


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def invoke(ctx: typer.Context, command_args: List[str]):
    """Invoke the plugin.

    Note: that if a command argument is a list, such as command_args, then
    unknown options are also included in the list and NOT stored in the context as usual.

    Args:
        ctx: The typer.Context for this invocation
        command_args: The command args to invoke
    """
    command_name, command_args = command_args[0], command_args[1:]
    log.debug(
        "called", command_name=command_name, command_args=command_args, env=os.environ
    )

    try:
        plugin.pre_invoke()
    except Exception as err:
        log.exception(
            "pre_invoke failed with uncaught exception, please report exception to maintainer"
        )
        sys.exit(1)

    try:
        plugin.invoke(command_name, command_args)
    except Exception as err:
        log.exception(
            "invoke failed with uncaught exception, please report exception to maintainer"
        )
        sys.exit(1)

    try:
        plugin.post_invoke()
    except Exception as err:
        log.exception(
            "ppost_invoke failed with uncaught exception, please report exception to maintainer"
        )
        sys.exit(1)


@app.command()
def describe(
    output_format: DescribeFormat = typer.Option(
        DescribeFormat.text, "--format", help="Output format"
    )
):
    """Describe the available commands of this extension."""
    try:
        plugin.describe(output_format)
    except Exception as err:
        log.exception(
            "describe failed with uncaught exception, please report exception to maintainer"
        )
        sys.exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, log_level: str = typer.Option("INFO", envvar="LOG_LEVEL")):
    """
    Manage users in the awesome CLI app.
    """
    default_logging_config(parse_log_level(log_level))
    if ctx.invoked_subcommand is None:
        log.info("echo bare invocation", env=os.environ, args=sys.argv)
