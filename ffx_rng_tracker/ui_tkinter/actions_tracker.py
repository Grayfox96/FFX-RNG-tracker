from itertools import islice
from typing import Callable

from ..data.characters import CHARACTERS
from ..data.constants import EncounterCondition
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.encounter import Encounter
from ..events.main import Event
from ..events.parsing import parse_action, parse_encounter, parse_stat_update
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
                case ['encounter', *params]:
                    if params and 'simulated'.startswith(params[0]):
                        type_ = 'simulated'
                        name = 'simulation_(mi\'ihen)'
                        forced_condition = 'normal'
                    else:
                        type_ = 'set'
                        name = 'klikk_1'
                        forced_condition = params[0] if params else 'normal'
                    line = f'encounter {type_} {name} false {forced_condition}'
                case [character, *params] if character in CHARACTERS:
                    line = ' '.join(['action', character, *params])
            input_lines[index] = line
        return '\n'.join(input_lines)

    def parse_input(self) -> None:
        self.gamestate.reset()
        events_sequence = self.parser.parse(self.get_input())

        output_data = []
        for event in events_sequence:
            match event:
                case Encounter():
                    line = ''
                    icvs = ' '.join([f'{c[:2]:2}[{icv:2}]'
                                     for c, icv
                                     in islice(event.icvs.items(), 7)])
                    if event.condition != EncounterCondition.NORMAL:
                        condition = f'{event.condition:10}'
                    elif event.name.startswith('simulation'):
                        condition = 'Simulation'
                    else:
                        condition = ' ' * 10
                    line = (f'Encounter {event.index:3}: {condition} {icvs}')
                    output_data.append(line)
                # if the text contains /// it hides the lines before it
                case Comment() if event.text == '///':
                    output_data.clear()
                case _:
                    output_data.append(str(event))

        # update the text widget
        self.print_output('\n'.join(output_data))
