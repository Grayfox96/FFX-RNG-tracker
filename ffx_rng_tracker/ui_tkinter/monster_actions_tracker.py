from typing import Callable

from ..data.monsters import MONSTERS
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.main import Event
from ..events.parsing import parse_monster_action, parse_party_change
from .base_widgets import BaseWidget


class MonsterActionsTracker(BaseWidget):

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            ('^.*changed to.+$', 'stat update', True),
            ('^#(.+?)?$', 'comment', True),
        ]
        tags.extend(super().get_tags())
        return tags

    def get_parsing_functions(self) -> dict[str, Callable[..., Event]]:
        parsing_functions = super().get_parsing_functions()
        parsing_functions['party'] = parse_party_change
        parsing_functions['monsteraction'] = parse_monster_action
        return parsing_functions

    def get_default_input_text(self) -> str:
        return get_notes('monster_actions_notes.txt', self.gamestate.seed)

    def get_input(self) -> str:
        input_data = super().get_input()
        input_lines = input_data.split('\n')
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case [monster, *params] if monster in MONSTERS:
                    line = ' '.join(['monsteraction', monster, *params])
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
