import re
from typing import Protocol

from ..configs import UITagConfigs


class OutputWidget(Protocol):
    """Protocol class for output widgets."""
    tags: dict[str, UITagConfigs]

    def print_output(self, output: str) -> None:
        """Prints the output data to the screen."""

    def highlight_pattern(self, tag_name: str, pattern: re.Pattern) -> None:
        """Apply the highlight options associated with tag_name
        to all occurrences of the pattern.
        """

    def clean_tag(self, tag_name: str) -> None:
        """Remove the highlight options associated with tag_name
        from the output.
        """

    def register_tag(self,
                     tag_name: str,
                     tag: UITagConfigs | None = None,
                     ) -> None:
        """Setup tag to be used in highlight_pattern.

        If tag is not provided, a tag with the name tag_name
        will be retrieved from Configs.ui_tags.
        """

    def seek(self, text: str) -> None:
        """Move the view of the output such that the first
        occurence of text is visible.
        """


class ConfirmationPopup(OutputWidget):
    confirmed: bool
