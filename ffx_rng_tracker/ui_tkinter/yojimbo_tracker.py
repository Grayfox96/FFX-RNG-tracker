from ..data.actions import YOJIMBO_ACTIONS
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.parsing import (parse_compatibility_update, parse_death,
                              parse_roll, parse_yojimbo_action)
from .base_widgets import BaseWidget


class YojimboTracker(BaseWidget):
    """Widget used to track Yojimbo rng."""

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            (' [0-9]{1,7}(?= gil) ', 'yojimbo low gil', True),
            (' [0-9]{10,}(?= gil) ', 'yojimbo high gil', True),
            ('^.*changed to.+$', 'stat update', True),
        ]
        tags.extend(super().get_tags())
        return tags

    def get_default_input_text(self) -> str:
        return get_notes('yojimbo_notes.txt', self.gamestate.seed)

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
                case ['compatibility', *params]:
                    event = parse_compatibility_update(gs, *params)
                case ['death', *_]:
                    event = parse_death(gs, 'yojimbo')
                case [action_name, *params] if action_name in YOJIMBO_ACTIONS:
                    event = parse_yojimbo_action(gs, action_name, *params)
                case [event_name, *_]:
                    event = Comment(gs, f'No event called {event_name!r}')

            self.gamestate.events_sequence.append(event)

        output_data = []
        for event in self.gamestate.events_sequence:
            match event:
                # if the text contains /// it hides the lines before it
                case Comment() if event.text == '///':
                    output_data.clear()
                case _:
                    output_data.append(str(event))

        # update the text widget
        self.print_output('\n'.join(output_data))
