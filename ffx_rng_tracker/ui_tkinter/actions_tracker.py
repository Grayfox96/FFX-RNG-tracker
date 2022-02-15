from ..data.characters import CHARACTERS
from ..data.constants import EncounterCondition
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.encounter import Encounter
from ..events.parsing import (parse_action, parse_encounter, parse_roll,
                              parse_stat_update)
from .base_widgets import BaseWidget, BetterText


class ActionsTracker(BaseWidget):
    """Widget used to track damage, critical chance,
    escape chance and miss chance rng.
    """

    def make_input_widget(self) -> BetterText:
        widget = super().make_input_widget()
        notes = get_notes('actions_notes.txt', self.gamestate.seed)
        widget.set(notes)
        return widget

    def get_input(self) -> None:
        self.gamestate.reset()
        input_lines = self.input_widget.get('1.0', 'end').split('\n')
        gs = self.gamestate
        # parse through the input text
        for line in input_lines:
            match line.lower().split():
                case []:
                    event = Comment(gs, line)
                case [*words] if words[0].startswith(('#', '///')):
                    event = Comment(gs, line)
                case [('roll' | 'waste' | 'advance'), *params]:
                    event = parse_roll(gs, *params)
                case ['encounter', *params]:
                    if params and 'simulated'.startswith(params[0]):
                        enc_type = 'simulated'
                        name = 'Simulation (Miihen)'
                        forced_condition = 'normal'
                    else:
                        enc_type = 'set'
                        name = 'Klikk 1'
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

    def print_output(self) -> None:
        self.get_input()
        data = []
        for event in self.gamestate.events_sequence:
            match event:
                # if the text contains /// it hides the lines before it
                case Comment() if event.text.startswith('///'):
                    data.clear()
                case Encounter():
                    icvs = ''
                    for index, (c, icv) in enumerate(event.icvs.items()):
                        if index >= 7:
                            break
                        icvs += f'{c[:2]}[{icv}] '
                    if event.condition == EncounterCondition.NORMAL:
                        condition = ''
                    else:
                        condition = str(event.condition)
                    data.append(
                        f'Encounter {event.index:3} {condition:10} {icvs}')
                case _:
                    data.append(str(event))

        # update the text widget
        self.output_widget.config(state='normal')
        self.output_widget.set('\n'.join(data))
        self.highlight_patterns()
        self.output_widget.config(state='disabled')
