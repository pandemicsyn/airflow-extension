from __future__ import annotations

import os
from copy import deepcopy


class ExtensionConfig:
    def __init__(self, extension_name: str, env_prefix: str | None = None):
        self.env_prefix = env_prefix.upper() or extension_name.upper()

    def cleaned_config_key(self, key: str) -> str:
        if key.startswith(self.env_prefix):
            return key[len(self.env_prefix) :]
        return None

    def load(self):
        config = {}
        for key, value in os.environ.items():
            cleaned_key = self.cleaned_config_key(key)
            if cleaned_key:
                config[cleaned_key] = value
        return config
