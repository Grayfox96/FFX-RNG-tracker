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
            words = line.lower().split()
            # if the line is empty or starts with # add it as a comment
            if words == [] or words[0][0] == '#' or words[0][:3] == '///':
                event = Comment(line)
            else:
                # if the line is not a comment use it to call a function
                event_name, *params = words
                if event_name in ('advance', 'roll', 'waste'):
                    event = parse_roll(*params)
                elif event_name == 'compatibility':
                    event = parse_compatibility_update(*params)
                elif event_name == 'death':
                    event = parse_death('yojimbo')
                else:
                    event = parse_yojimbo_action(*words)
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
