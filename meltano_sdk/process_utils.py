"""Utilities for working with subprocesses."""

from __future__ import annotations

import asyncio
import subprocess
from asyncio.subprocess import PIPE

import structlog

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

        Note that output from stdout and stderr is NOT logged automatically. Especially useful when you want to run a
        command, but don't care about its output and only care about its return code.

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

    def run_and_log(self, sub_command: str | None = None, *args) -> None:
        """Run a subprocess and stream the output to the logger.

        Note that output from stdout and stderr is logged by default. Best used when you want to run a command and
        stream the output to a user.

        Args:
            sub_command: The subcommand to run.
            *args: The arguments to pass to the subprocess.

        Raises:
            subprocess.CalledProcessError: If the subprocess failed.
        """

        async def _log_stdio(reader: asyncio.streams.StreamReader):
            while True:
                if reader.at_eof():
                    break
                data = await reader.readline()
                log.info(data.decode("utf-8").rstrip())
                await asyncio.sleep(0)

        async def _exec() -> asyncio.subprocess.Process:
            popen_args = []
            if sub_command:
                popen_args.append(sub_command)
            if args:
                popen_args.extend(*args)

            p = await asyncio.create_subprocess_exec(
                self.bin, *popen_args, stdout=PIPE, stderr=PIPE, env=self.popen_env
            )
            asyncio.create_task(_log_stdio(p.stderr))
            asyncio.create_task(_log_stdio(p.stdout))

            await p.wait()
            return p

        result = asyncio.run(_exec())
        if result.returncode:
            raise subprocess.CalledProcessError(
                result.returncode, cmd=self.bin, stderr=None
            )
