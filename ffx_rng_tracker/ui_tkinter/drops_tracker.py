from ..data.monsters import MONSTERS
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.parsing import (parse_bribe, parse_death, parse_kill,
                              parse_party_change, parse_roll, parse_steal)
from .base_widgets import BaseWidget, BetterText


class DropsTracker(BaseWidget):
    """Widget used to track monster drops RNG."""

    def make_input_widget(self) -> BetterText:
        widget = super().make_input_widget()
        notes = get_notes('drops_notes.txt', self.gamestate.seed)
        widget.set(notes)
        return widget

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            ('Equipment', 'equipment', False),
            ('No Encounters', 'no encounters', False),
            ('^#(.+?)?$', 'comment', True),
            ('^.*changed to.+$', 'stat update', True),
        ]
        tags.extend(super().get_tags())
        return tags

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
                case ['steal', *params]:
                    event = parse_steal(gs, *params)
                case ['kill', *params]:
                    event = parse_kill(gs, *params)
                case ['death', *params]:
                    event = parse_death(gs, *params)
                case ['party', *params]:
                    event = parse_party_change(gs, *params)
                case ['bribe', *params]:
                    event = parse_bribe(gs, *params)
                case [monster_name, *params] if monster_name in MONSTERS:
                    event = parse_kill(gs, monster_name, *params)
                case [event_name, *_]:
                    event = Comment(gs, f'No event called {event_name!r}')

            self.gamestate.events_sequence.append(event)

    def print_output(self):
        self.get_input()
        data = []
        for event in self.gamestate.events_sequence:
            match event:
                # if the text contains /// it hides the lines before it
                case Comment() if event.text.startswith('///'):
                    data.clear()
                case _:
                    data.append(str(event))

        self.output_widget.config(state='normal')
        self.output_widget.set('\n'.join(data))
        self.highlight_patterns()
        self.output_widget.config(state='disabled')
