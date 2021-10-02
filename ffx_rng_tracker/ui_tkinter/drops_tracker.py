from ..data.file_functions import get_notes
from ..events import Comment
from ..ui_functions import (parse_death, parse_kill, parse_party_change,
                            parse_roll, parse_steal)
from .base_widgets import BaseWidget, BetterText


class DropsTracker(BaseWidget):
    """Widget used to track enemy drops RNG."""

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
            words = line.lower().split()
            # if the line is empty or starts with # add it as a comment
            if words == [] or words[0][0] == '#' or words[0][:3] == '///':
                event = Comment(line)
            else:
                event_name, *params = words
                if event_name == 'steal':
                    event = parse_steal(*params)
                elif event_name == 'kill':
                    event = parse_kill(*params)
                elif event_name == 'death':
                    event = parse_death(*params)
                elif event_name in ('roll', 'waste', 'advance'):
                    event = parse_roll(*params)
                elif event_name == 'party':
                    event = parse_party_change(*params)
                else:
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
        self.output_widget.config(state='disabled')

        self.output_widget.highlight_pattern('Equipment', 'blue')
        self.output_widget.highlight_pattern('No Encounters', 'green')
        self.output_widget.highlight_pattern('^#(.+?)?$', 'gray', regexp=True)
        self.output_widget.highlight_pattern(
            '^Advanced rng.+$', 'red', regexp=True)
        # highlight error messages
        error_messages = (
            'Invalid', 'No event called', 'Usage:', 'No monster named',
            'Can\'t advance', 'No character named',
        )
        for error_message in error_messages:
            self.output_widget.highlight_pattern(
                f'^{error_message}.+$', 'red_background', regexp=True)
        self.output_widget.highlight_pattern(
            '^.+$', 'wrap_margin', regexp=True)
