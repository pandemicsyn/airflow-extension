from __future__ import annotations

import asyncio
import os
import sys

import structlog

"""Utilities for working with subprocesses."""

import subprocess

log = structlog.get_logger()


def log_subprocess_error(
    cmd: str, err: subprocess.CalledProcessError, error_message: str
):
    """Log a subprocess error, replaying stderr to the logger in the process"""
    if err.stderr:
        for line in err.stderr.split("\n"):
            log.warning(line, cmd=cmd, stdio_stream="stderr")
    log.error(
        f"error invoking {cmd}",
        returncode=err.returncode,
        error_message=error_message,
    )


class Invoker:
    def __init__(
        self,
        bin: str,
        universal_newlines: bool = True,
        cwd: str = None,
        env: dict[str, any] | None = None,
    ):
        """Minimal invoker for running subprocesses.

        Args:
            bin: The name of the binary to run.
            universal_newlines: Whether to use universal newlines.
            cwd: The working directory to run from.
            env: Env to use when calling Popen.
        """
        self.bin = bin
        self.universal_newlines = universal_newlines
        self.cwd = cwd
        self.popen_env = env

    def run(
        self, *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) -> subprocess.CompletedProcess:
        """Run a subprocess. Simple wrapper around subprocess.run.

        Note that output from stdout and stderr is not proactively logged. Best used when you do not need to show
        the output to an end user.

        Args:
            *args: The arguments to pass to the subprocess.
            stdout: The stdout stream to use. If you do not want to capture stdout, use subprocess.DEVNULL.
            stderr: The stderr stream to use. If you do not want to capture stderr, use subprocess.DEVNULL.

        Returns:
            The completed process.

        Raises:
            subprocess.CalledProcessError: If the subprocess failed.
        """

        return subprocess.run(
            [self.bin, *args],
            cwd=self.cwd,
            universal_newlines=self.universal_newlines,
            stdout=stdout,
            stderr=stderr,
            check=True,
        )

    def run_stream(self, *args) -> None:
        """Run a subprocess and stream the output to the logger.

        Args:
            *args: The arguments to pass to the subprocess.

        Returns:
            The completed process.

        Raises:
            subprocess.CalledProcessError: If the subprocess failed.
        """
        p = subprocess.Popen(
            [self.bin, *args],
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=self.popen_env,
        )
        while p.poll() is None:
            log.info(p.stdout.readline().decode("utf-8").rstrip())
        log.info(p.stdout.readline().decode("utf-8").rstrip())
        if p.returncode:
            raise subprocess.CalledProcessError(p.returncode, p.args)