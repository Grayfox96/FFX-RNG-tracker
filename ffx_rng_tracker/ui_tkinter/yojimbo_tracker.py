from ffx_rng_tracker.data.actions import YOJIMBO_ACTIONS
from ..data.file_functions import get_notes
from ..events.comment import Comment
from ..ui_functions import (parse_compatibility_update, parse_death,
                            parse_roll, parse_yojimbo_action)
from .base_widgets import BaseWidget, BetterText


class YojimboTracker(BaseWidget):
    """Widget used to track Yojimbo rng."""

    def __init__(self, parent, *args, **kwargs):
        self.default_notes = get_notes('yojimbo_notes.txt')
        super().__init__(parent, *args, **kwargs)

    def make_input_widget(self) -> BetterText:
        widget = super().make_input_widget()
        widget.insert('end', self.default_notes)
        return widget

    def set_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            (' [0-9]{1,7}(?= gil) ', 'yojimbo low gil', True),
            (' [0-9]{10,}(?= gil) ', 'yojimbo high gil', True),
            ('^.*changed to.+$', 'stat update', True),
        ]
        tags.extend(super().set_tags())
        return tags

    def get_input(self):
        # reset variables to the initial state
        self.rng_tracker.reset()
        # get notes
        notes_lines = self.input_widget.get('1.0', 'end').split('\n')
        # parse notes
        for line in notes_lines:
            match line.lower().split():
                case []:
                    event = Comment(line)
                case [*words] if words[0].startswith(('#', '///')):
                    event = Comment(line)
                case [('roll' | 'waste' | 'advance'), *params]:
                    event = parse_roll(*params)
                case ['compatibility', *params]:
                    event = parse_compatibility_update(*params)
                case ['death', *_]:
                    event = parse_death('yojimbo')
                case [action_name, *params] if action_name in YOJIMBO_ACTIONS:
                    event = parse_yojimbo_action(action_name, *params)
                case [event_name, *_]:
                    event = Comment(f'No event called {event_name!r}')

            self.rng_tracker.events_sequence.append(event)

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
