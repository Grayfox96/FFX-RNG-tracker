from typing import Callable

from ..data.characters import CHARACTERS
from ..data.notes import get_notes
from ..events.main import Event
from ..events.parsing_functions import (parse_action, parse_encounter,
                                        parse_stat_update)
from .base_widgets import BaseWidget


class ActionsTracker(BaseWidget):
    """Widget used to track damage, critical chance,
    escape chance and miss chance rng.
    """

    def get_tags(self) -> dict[str, str]:
        tags = {
            'encounter': 'Encounter',
            'preemptive': 'Preemptive',
            'ambush': 'Ambush',
            'crit': 'Crit',
            'stat update': '^.*changed to.+$',
        }
        tags.update(super().get_tags())
        return tags

    def get_default_input_text(self) -> str:
        return get_notes('actions_notes.txt', self.gamestate.seed)

    def get_parsing_functions(self) -> dict[str, Callable[..., Event]]:
        parsing_functions = super().get_parsing_functions()
        parsing_functions['encounter'] = parse_encounter
        parsing_functions['stat'] = parse_stat_update
        parsing_functions['action'] = parse_action
        return parsing_functions

    def get_input(self) -> str:
        input_data = super().get_input()
        input_lines = input_data.split('\n')
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case ['encounter', condition, *_]:
                    type_ = 'boss'
                    if 'simulated'.startswith(condition):
                        type_ = 'simulated'
                        name = 'simulation_(dummy)'
                    elif 'preemptive'.startswith(condition):
                        name = 'dummy_preemptive'
                    elif 'ambush'.startswith(condition):
                        name = 'dummy_ambush'
                    else:
                        name = 'dummy'
                    line = f'encounter {type_} {name} false'
                case ['encounter']:
                    line = 'encounter boss dummy false'
                case [character, *params] if character in CHARACTERS:
                    line = ' '.join(['action', character, *params])
            input_lines[index] = line
        return '\n'.join(input_lines)

    def parse_input(self) -> None:
        self.gamestate.reset()
        events_sequence = self.parser.parse(self.get_input())

        output_data = []
        for event in events_sequence:
            line = str(event)
            output_data.append(line)
            # if the text contains /// it hides the lines before it
            if line == '///':
                output_data.clear()

        data = '\n'.join(output_data)
        data = data.replace(' - Simulation: Dummy Normal', ': Simulation')
        data = data.replace(' - Boss: Dummy', ':')
        data = data.replace('Normal', '          ')
        data = data.replace('Ambush', 'Ambush    ')

        # update the text widget
        self.print_output(data)
