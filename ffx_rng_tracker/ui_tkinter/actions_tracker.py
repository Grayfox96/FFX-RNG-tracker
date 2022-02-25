from itertools import islice

from ..data.characters import CHARACTERS
from ..data.constants import EncounterCondition
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.encounter import Encounter
from ..events.parsing import (parse_action, parse_encounter, parse_roll,
                              parse_stat_update)
from .base_widgets import BaseWidget


class ActionsTracker(BaseWidget):
    """Widget used to track damage, critical chance,
    escape chance and miss chance rng.
    """

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            ('Encounter', 'encounter', False),
            ('Preemptive', 'preemptive', False),
            ('Ambush', 'ambush', False),
            ('Crit', 'crit', False),
            ('^.*changed to.+$', 'stat update', True),
            ('^#(.+?)?$', 'comment', True),
        ]
        tags.extend(super().get_tags())
        return tags

    def get_default_input_text(self) -> str:
        return get_notes('actions_notes.txt', self.gamestate.seed)

    def parse_input(self) -> None:
        input_data = self.get_input()
        input_lines = input_data.split('\n')

        gs = self.gamestate
        gs.reset()

        # parse through the input text
        for line in input_lines:
            match line.lower().split():
                case words if not words or words[0].startswith(('#', '///')):
                    event = Comment(gs, line)
                case [('roll' | 'waste' | 'advance'), *params]:
                    event = parse_roll(gs, *params)
                case ['encounter', *params]:
                    if params and 'simulated'.startswith(params[0]):
                        enc_type = 'simulated'
                        name = 'simulation_(mi\'ihen)'
                        forced_condition = 'normal'
                    else:
                        enc_type = 'set'
                        name = 'klikk_1'
                        forced_condition = params[0] if params else 'normal'
                    event = parse_encounter(
                        gs, enc_type, name, '', forced_condition)
                case ['stat', *params]:
                    event = parse_stat_update(gs, *params)
                case [character, *params] if character in CHARACTERS:
                    event = parse_action(gs, character, *params)
                case [event_name, *_]:
                    event = Comment(gs, f'No event called {event_name!r}')

            self.gamestate.events_sequence.append(event)

        output_data = []
        for event in self.gamestate.events_sequence:
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
