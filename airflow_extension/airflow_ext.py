from __future__ import annotations

import configparser
import os
import subprocess
import sys
from pathlib import Path

import click
import structlog

from meltano_sdk.config import ExtensionConfig
from meltano_sdk.extension_base import ExtensionBase
from meltano_sdk.process_utils import Invoker, log_subprocess_error

log = structlog.get_logger()


class Airflow(ExtensionBase):
    def __init__(self):

        self.airflow_bin = "airflow"
        self.airflow_invoker = Invoker(self.airflow_bin)

        self.app_name = "airflow_extension"

        self.airflow_home = os.environ.get("AIRFLOW_HOME") or os.environ.get(
            f"{self.app_name}_AIRFLOW_HOME"
        )
        if not self.airflow_home:
            log.debug("env dump", env=os.environ)
            log.error(
                "AIRFLOW_HOME not found in environment, unable to function without it"
            )
            sys.exit(1)

        self.airflow_cfg_path = Path(os.environ.get("AIRFLOW_CONFIG"))
        if not self.airflow_cfg_path:
            log.debug("env dump", env=os.environ)
            log.error(
                "AIRFLOW_CONFIG not found in environment, unable to function without it"
            )
            sys.exit(1)
        if not self.airflow_cfg_path.exists():
            log.warning(
                "airflow.cfg does not exist, will be auto-generated with defaults",
                airflow_cfg_path=self.airflow_cfg_path,
            )

        # Configure the env to make airflow installable without GPL deps.
        os.environ["SLUGIFY_USES_TEXT_UNIDECODE"] = "yes"

        self.env_config = ExtensionConfig("airflow", "AIRFLOW_").load()
        log.debug("Loaded env config", env_config=self.env_config)

    def pre_invoke(self):
        self._create_config()
        # self._update_config()
        self._initdb()

    @staticmethod
    def post_invoke():
        log.debug("post_invoke")

    def invoke(self, command_name: str | None, *command_args):
        try:
            result = self.airflow_invoker.run_stream(command_name)
        except subprocess.CalledProcessError as err:
            log_subprocess_error(
                f"airflow {command_name}", err, "airflow invocation failed"
            )
            sys.exit(1)

    def describe(self):
        commands = ["pre_invoke", "post_invoke", "invoke", "about", "describe"]
        click.echo({"commands": commands})

    def _create_config(self):
        # create an initial airflow config file
        try:
            self.airflow_invoker.run("--help", stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError as err:
            log_subprocess_error(
                "airflow --help", err, "initial airflow invocation failed"
            )
            sys.exit(1)

    def _update_config(self):
        # open the configuration and update it
        # now we let's update the config to use our stubs
        airflow_cfg = configparser.ConfigParser()

        with self.airflow_cfg_path.open() as airflow_cfg_file_to_read:
            airflow_cfg.read_file(airflow_cfg_file_to_read)
            log.debug("Loaded airflow cfg", config_path={str(self.airflow_cfg_path)})

        for section, section_config in self.env_config.items():
            airflow_cfg[section].update(section_config)
            log.debug(
                "Updated airflow cfg section",
                section=section,
                section_config=section_config,
            )

        with self.airflow_cfg_path.open("w") as airflow_cfg_file_to_write:
            airflow_cfg.write(airflow_cfg_file_to_write)
            log.debug("Saved airflow cfg", config_path={str(self.airflow_cfg_path)})

    def _initdb(self):
        """Initialize the airflow metadata database."""
        try:
            result = self.airflow_invoker.run("db", "init")
        except subprocess.CalledProcessError as err:
            log_subprocess_error("airflow db init", err, "airflow db init failed")
            sys.exit(1)

    def _cleanup(self):
        try:
            self.airflow_cfg_path.unlink()
            log.debug("Removed airflow cfg", config_path={str(self.airflow_cfg_path)})
        except FileNotFoundError:
            pass
