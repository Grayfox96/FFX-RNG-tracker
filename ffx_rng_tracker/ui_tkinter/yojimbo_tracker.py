from typing import Callable

from ..data.actions import YOJIMBO_ACTIONS
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.main import Event
from ..events.parsing import (parse_compatibility_update, parse_death,
                              parse_yojimbo_action)
from .base_widgets import BaseWidget


class YojimboTracker(BaseWidget):
    """Widget used to track Yojimbo rng."""

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            (' [0-9]{1,7}(?= gil) ', 'yojimbo low gil', True),
            (' [0-9]{10,}(?= gil) ', 'yojimbo high gil', True),
            ('^.*changed to.+$', 'stat update', True),
        ]
        tags.extend(super().get_tags())
        return tags

    def get_parsing_functions(self) -> dict[str, Callable[..., Event]]:
        parsing_functions = super().get_parsing_functions()
        parsing_functions['death'] = parse_death
        parsing_functions['compatibility'] = parse_compatibility_update
        parsing_functions['yojimboaction'] = parse_yojimbo_action
        return parsing_functions

    def get_default_input_text(self) -> str:
        return get_notes('yojimbo_notes.txt', self.gamestate.seed)

    def get_input(self) -> str:
        input_data = super().get_input()
        input_lines = input_data.split('\n')
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case ['death', *_]:
                    line = 'death yojimbo'
                case [action_name, *params] if action_name in YOJIMBO_ACTIONS:
                    line = ' '.join(['yojimboaction', action_name, *params])
            input_lines[index] = line
        return '\n'.join(input_lines)

    def parse_input(self) -> None:
        self.gamestate.reset()
        events_sequence = self.parser.parse(self.get_input())

        output_data = []
        for event in events_sequence:
            match event:
                # if the text contains /// it hides the lines before it
                case Comment() if event.text == '///':
                    output_data.clear()
                case _:
                    output_data.append(str(event))

        # update the text widget
        self.print_output('\n'.join(output_data))
