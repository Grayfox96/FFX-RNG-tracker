from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..events.parser import EventParser
from .input_widget import InputWidget
from .output_widget import OutputWidget


@dataclass
class BaseTracker(ABC):
    parser: EventParser
    input_widget: InputWidget
    output_widget: OutputWidget
    previous_input_text: str = field(default='', init=False, repr=False)
    previous_output_text: str = field(default='', init=False, repr=False)

    def __post_init__(self) -> None:
        self.input_widget.set_input(self.get_default_input_data())

    @abstractmethod
    def get_default_input_data(self) -> str:
        """Returns the default input data."""

    @abstractmethod
    def edit_input(self, input_text: str) -> str:
        """Edits the input text to adhere to the parser's syntax."""

    @abstractmethod
    def edit_output(self, output: str) -> str:
        """Edits the output before being sent to the output widget."""

    def callback(self, *_, **__) -> None:
        """Method called as a ui callback to parse the input
        and print it to screen.
        If the input has not changed since the last time this method
        was called it does nothing.
        If the output has not changed since the last time this method
        was called it will not be sent to the output widget.
        """
        input_text = self.input_widget.get_input()
        if self.previous_input_text == input_text:
            return
        self.previous_input_text = input_text
        self.parser.gamestate.reset()
        edited_input = self.edit_input(input_text)
        output = [str(e) for e in self.parser.parse(edited_input)]
        edited_output = self.edit_output('\n'.join(output))
        if self.previous_output_text == edited_output:
            return
        self.previous_output_text = edited_output
        self.output_widget.print_output(edited_output)
