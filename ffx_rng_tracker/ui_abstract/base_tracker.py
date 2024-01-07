from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..data.notes import get_notes, save_notes
from ..events.main import Event
from ..events.parser import EventParser
from ..events.parsing_functions import USAGE, ParsingFunction, parse_roll
from .input_widget import InputWidget
from .output_widget import ConfirmationPopup, OutputWidget


@dataclass
class TrackerUI(ABC):
    parser: EventParser
    input_widget: InputWidget
    output_widget: OutputWidget
    warning_popup: OutputWidget
    confirmation_popup: ConfirmationPopup
    previous_input_text: str = field(default='', init=False, repr=False)
    previous_output_text: str = field(default='', init=False, repr=False)
    notes_file: str = field(default='', init=False, repr=False)
    usage: str = field(default='', init=False, repr=False)

    def __post_init__(self) -> None:
        for function in self.get_parsing_functions():
            for usage_string in USAGE[function]:
                command = usage_string.split()[0]
                self.parser.register_parsing_function(command, function)
        self.usage = self.get_usage()
        self.input_widget.set_input(self.get_default_input_data())
        self.input_widget.register_callback(self.callback)
        self.callback()

    def get_default_input_data(self) -> str:
        """Returns the default input data."""
        return get_notes(self.notes_file, self.parser.gamestate.seed)

    @abstractmethod
    def get_parsing_functions(self) -> list[ParsingFunction]:
        """Returns a list of parsing functions."""

    def get_usage(self) -> str:
        usage_lines = ['# Usage:']
        for function in self.get_parsing_functions():
            if function is parse_roll:
                continue
            usage_lines.extend(USAGE.get(function, []))
        return '\n#     '.join(usage_lines)

    @abstractmethod
    def edit_input(self, input_text: str) -> str:
        """Edits the input text to adhere to the parser's syntax."""

    def events_to_string(self, events: list[Event]) -> str:
        """Converts a list of events to a string."""
        return '\n'.join([str(e) for e in events])

    def get_paddings(self,
                     split_lines: list[list[str]],
                     ) -> dict[str, dict[int, int]]:
        paddings: dict[str, dict[int, int]] = {}
        for event_name, *line_parts in split_lines:
            if not line_parts:
                continue
            event_paddings = paddings.setdefault(event_name, {})
            for i, line_part in enumerate(line_parts):
                event_paddings[i] = max(
                    event_paddings.get(i, 0), len(line_part))
        return paddings

    def pad_output(self, output: str) -> str:
        split_lines: list[list[str]] = []
        for line in output.splitlines():
            event_name, *line_parts = line.split(':')
            if not any(line_parts):
                split_lines.append([line])
                continue
            line_parts = ':'.join(line_parts).split('|')
            split_lines.append([event_name] + line_parts)
        paddings = self.get_paddings(split_lines)
        lines = []
        for event_name, *line_parts in split_lines:
            if not line_parts:
                lines.append(event_name)
                continue
            if event_name not in paddings:
                lines.append(f'{event_name}:{'|'.join(line_parts)}')
                continue
            parts = []
            for i, line_part in enumerate(line_parts):
                parts.append(f'{line_part:{paddings[event_name][i]}}')
            lines.append(f'{event_name}:{'|'.join(parts)}'.rstrip())
        return '\n'.join(lines)

    @abstractmethod
    def edit_output(self, output: str, padding: bool = False) -> str:
        """Edits the output before being sent to the output widget.

        If padding is set to True the method pad_output might be called
        with output as the parameter
        """

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
        output = self.events_to_string(self.parser.parse(edited_input))
        padding = '# Command: /nopadding\n' not in output
        edited_output = self.edit_output(output, padding)
        if self.previous_output_text == edited_output:
            return
        self.previous_output_text = edited_output
        self.output_widget.print_output(edited_output)

    def save_input_data(self) -> None:
        seed = self.parser.gamestate.seed
        try:
            save_notes(self.notes_file, seed, self.input_widget.get_input())
        except FileExistsError as error:
            self.confirmation_popup.print_output(
                f'Do you want to overwrite file {error.args[0]!r}?')
            if self.confirmation_popup.confirmed:
                save_notes(
                    self.notes_file, seed, self.input_widget.get_input(),
                    force=True)
                self.warning_popup.print_output(
                    f'File "{seed}_{self.notes_file}" '
                    'saved successfully!')
        else:
            self.warning_popup.print_output(
                f'File "{seed}_{self.notes_file}" saved successfully!')
