import json
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List, Optional

import yaml
from pydantic import BaseModel


class DescribeFormat(str, Enum):
    text = "text"
    json = "json"
    yaml = "yaml"


class Description(BaseModel):
    commands: List[str] = [":splat"]


class ExtensionBase(metaclass=ABCMeta):
    """Basic extension base class that all extensions should inherit from and satisfy."""

    @abstractmethod
    def invoke(self) -> None:
        """Invoke method.

        This method is called when the plugin is invoked.
        """
        pass

    @abstractmethod
    def describe(self) -> Description:
        """Describe method.

        This method should describe what commands and capabilities the extension provides.

        Returns:
            Description: A description of the extension.
        """
        pass

    def describe_formatted(
        self, output_format: DescribeFormat = DescribeFormat.text
    ) -> str:
        """Return a formatted description of the extensions commands and capabilities.

        Args:
            output_format: The output format to use.

        Returns:
            str: The formatted description.
        """
        if output_format == DescribeFormat.text:
            return f"commands: {self.describe().commands}"
        elif output_format == DescribeFormat.json:
            return json.dumps(self.describe().dict(), indent=2)
        elif output_format == DescribeFormat.yaml:
            return yaml.dump(self.describe().dict())
