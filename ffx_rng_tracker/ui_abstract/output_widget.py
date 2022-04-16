from typing import Protocol


class OutputWidget(Protocol):
    """Protocol class for output widgets."""

    def print_output(self, output: str) -> None:
        """Prints the output data to the screen."""
