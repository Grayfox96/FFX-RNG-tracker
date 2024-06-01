import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field

from ..configs import REGEX_NEVER_MATCH, UITagConfigs, UIWidgetConfigs
from ..data.notes import get_notes, save_notes
from ..events.parser import EventParser
from ..events.parsing_functions import USAGE, ParsingFunction, parse_roll
from .input_widget import InputWidget
from .output_widget import ConfirmPopup, OutputWidget, WarningPopup


@dataclass
class TrackerUI(ABC):
    configs: UIWidgetConfigs
    parser: EventParser
    input_widget: InputWidget
    output_widget: OutputWidget
    search_bar: InputWidget
    warning_popup: WarningPopup
    confirmation_popup: ConfirmPopup
    previous_edited_input: str = field(default='', init=False, repr=False)
    previous_edited_output: str = field(default='', init=False, repr=False)
    notes_file: str = field(default='', init=False, repr=False)
    usage: str = field(default='', init=False, repr=False)

    def __post_init__(self) -> None:
        for function in self.get_parsing_functions():
            for usage_string in USAGE[function]:
                command = usage_string.split()[0]
                self.parser.parsing_functions[command] = function
        self.usage = self.get_usage()
        self.input_widget.set_input(self.get_default_input_data())
        self.input_widget.register_callback(self.callback)
        for name in self.configs.tag_names:
            self.output_widget.register_tag(name)
        self.output_widget.register_tag(
            '#search bar',
            UITagConfigs(REGEX_NEVER_MATCH, background='#ffff00'),
            )
        self.search_bar.register_callback(self.search_callback)

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

    def get_paddings(self,
                     split_lines: list[list[str]],
                     ) -> dict[str, dict[int, int]]:
        paddings: dict[str, dict[int, int]] = defaultdict(dict)
        for event_name, *line_parts in split_lines:
            if not line_parts:
                continue
            event_paddings = paddings[event_name]
            for i, line_part in enumerate(line_parts):
                event_paddings[i] = max(
                    event_paddings.get(i, 0), len(line_part))
        return paddings

    def pad_output(self, output: str) -> str:
        split_lines: list[list[str]] = []
        for line in output.splitlines():
            if ':' not in line:
                split_lines.append([line])
                continue
            event_name, rest = line.split(':', 1)
            if not rest:
                split_lines.append([line])
                continue
            split_lines.append([event_name] + rest.split('|'))
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

    def callback(self) -> None:
        """Method called as a ui callback to parse the input
        and print it to screen.
        If the input has not changed since the last time this method
        was called it does nothing.
        If the output has not changed since the last time this method
        was called it will not be sent to the output widget.
        """
        edited_input = self.edit_input(self.input_widget.get_input())
        if self.previous_edited_input == edited_input:
            edited_output = self.previous_edited_output
        else:
            self.previous_edited_input = edited_input
            self.parser.gamestate.reset()
            output = self.parser.parse_to_string(edited_input)
            padding = 'Command: /nopadding\n' not in output
            edited_output = self.edit_output(output, padding)
            self.previous_edited_output = edited_output
        self.output_widget.print_output(edited_output)

    def search_callback(self) -> None:
        search = self.search_bar.get_input()
        self.output_widget.seek(search)
        tag = self.output_widget.tags['#search bar']
        self.output_widget.clean_tag('#search bar')
        if not search:
            tag.regex_pattern = REGEX_NEVER_MATCH
            return
        tag.regex_pattern = re.compile(re.escape(search), flags=re.IGNORECASE)
        self.output_widget.highlight_pattern('#search bar', tag.regex_pattern)

    def save_input_data(self) -> None:
        seed = self.parser.gamestate.seed
        try:
            save_notes(self.notes_file, seed, self.input_widget.get_input())
        except FileExistsError as error:
            confirmed = self.confirmation_popup.print_output(
                f'Do you want to overwrite file {error.args[0]!r}?')
            if confirmed:
                save_notes(
                    self.notes_file, seed, self.input_widget.get_input(),
                    force=True)
                self.warning_popup.print_output(
                    f'File "{seed}_{self.notes_file}" '
                    'saved successfully!')
        else:
            self.warning_popup.print_output(
                f'File "{seed}_{self.notes_file}" saved successfully!')
