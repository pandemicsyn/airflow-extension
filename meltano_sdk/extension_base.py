from abc import ABCMeta, abstractmethod
from enum import Enum


class DescribeFormat(str, Enum):
    text = "text"
    json = "json"
    yaml = "yaml"


class ExtensionBase(metaclass=ABCMeta):
    """Basic extension base class that all extensions should inherit from and satisfy."""

    @abstractmethod
    def invoke(self) -> None:
        """Invoke method.

        This method is called when the plugin is invoked.
        """
        pass

    @abstractmethod
    def describe(self, output_format: DescribeFormat = DescribeFormat.text) -> None:
        """Describe method.

        This method is called when the plugin is invoked with the --describe flag.
        """
        pass
