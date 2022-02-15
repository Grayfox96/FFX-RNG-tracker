from ..data.actions import YOJIMBO_ACTIONS
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.parsing import (parse_compatibility_update, parse_death,
                              parse_roll, parse_yojimbo_action)
from .base_widgets import BaseWidget, BetterText


class YojimboTracker(BaseWidget):
    """Widget used to track Yojimbo rng."""

    def make_input_widget(self) -> BetterText:
        widget = super().make_input_widget()
        notes = get_notes('yojimbo_notes.txt', self.gamestate.seed)
        widget.set(notes)
        return widget

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            (' [0-9]{1,7}(?= gil) ', 'yojimbo low gil', True),
            (' [0-9]{10,}(?= gil) ', 'yojimbo high gil', True),
            ('^.*changed to.+$', 'stat update', True),
        ]
        tags.extend(super().get_tags())
        return tags

    def get_input(self):
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
                case ['compatibility', *params]:
                    event = parse_compatibility_update(gs, *params)
                case ['death', *_]:
                    event = parse_death(gs, 'yojimbo')
                case [action_name, *params] if action_name in YOJIMBO_ACTIONS:
                    event = parse_yojimbo_action(gs, action_name, *params)
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
