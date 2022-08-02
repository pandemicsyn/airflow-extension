import os
import sys
from typing import List

import structlog
import typer

from airflow_extension.airflow_ext import Airflow
from meltano_sdk.extension_base import DescribeFormat
from meltano_sdk.logging import default_logging_config, parse_log_level

log = structlog.get_logger()

APP_NAME: str = "airflow_extension"

plugin = Airflow()
app = typer.Typer(pretty_exceptions_enable=False)


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
        typer.echo(plugin.describe_formatted(output_format))
    except Exception as err:
        log.exception(
            "describe failed with uncaught exception, please report exception to maintainer"
        )
        sys.exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    log_level: str = typer.Option("INFO", envvar="LOG_LEVEL"),
):
    """
    Simple Meltano extension to wrap the airflow CLI.
    """
    default_logging_config(parse_log_level(log_level))
    if ctx.invoked_subcommand is None:
        log.debug("called without subcommand, defaulting to describe")
        plugin.describe()
