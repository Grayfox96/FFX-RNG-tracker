from ffx_rng_tracker.data.monsters import MONSTERS

from ..data.file_functions import get_notes
from ..events.comment import Comment
from ..ui_functions import (parse_bribe, parse_death, parse_kill,
                            parse_party_change, parse_roll, parse_steal)
from .base_widgets import BaseWidget, BetterText


class DropsTracker(BaseWidget):
    """Widget used to track monster drops RNG."""

    def __init__(self, parent, *args, **kwargs):
        self.default_notes = get_notes('drops_notes.txt')
        super().__init__(parent, *args, **kwargs)

    def make_input_widget(self) -> BetterText:
        widget = super().make_input_widget()
        widget.insert('end', self.default_notes)
        return widget

    def get_input(self) -> None:
        input_lines = self.input_widget.get('1.0', 'end').split('\n')
        self.rng_tracker.reset()
        # parse through the input text
        for line in input_lines:
            match line.lower().split():
                case []:
                    event = Comment(line)
                case [*words] if words[0].startswith(('#', '///')):
                    event = Comment(line)
                case [('roll' | 'waste' | 'advance'), *params]:
                    event = parse_roll(*params)
                case ['steal', *params]:
                    event = parse_steal(*params)
                case ['kill', *params]:
                    event = parse_kill(*params)
                case ['death', *params]:
                    event = parse_death(*params)
                case ['party', *params]:
                    event = parse_party_change(*params)
                case ['bribe', *params]:
                    event = parse_bribe(*params)
                case [monster_name, *params] if monster_name in MONSTERS:
                    event = parse_kill(monster_name, *params)
                case [event_name, *_]:
                    event = Comment(f'No event called {event_name!r}')

            self.rng_tracker.events_sequence.append(event)

    def set_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            ('Equipment', 'equipment', False),
            ('No Encounters', 'no encounters', False),
            ('^#(.+?)?$', 'comment', True),
            ('^.*changed to.+$', 'stat update', True),
        ]
        tags.extend(super().set_tags())
        return tags

    def print_output(self):
        self.get_input()
        data = []
        for event in self.rng_tracker.events_sequence:
            line = str(event)
            # if the text contains /// it hides the lines before it
            if '///' in line:
                data.clear()
            else:
                data.append(line)

        data = '\n'.join(data)

        self.output_widget.config(state='normal')
        self.output_widget.set(data)
        self.highlight_patterns()
        self.output_widget.config(state='disabled')
