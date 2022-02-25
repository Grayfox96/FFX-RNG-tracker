from ..data.monsters import MONSTERS
from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.parsing import (parse_bribe, parse_death, parse_kill,
                              parse_party_change, parse_roll, parse_steal)
from .base_widgets import BaseWidget


class DropsTracker(BaseWidget):
    """Widget used to track monster drops RNG."""

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            ('Equipment', 'equipment', False),
            ('No Encounters', 'no encounters', False),
            ('^#(.+?)?$', 'comment', True),
            ('^.*changed to.+$', 'stat update', True),
        ]
        tags.extend(super().get_tags())
        return tags

    def get_default_input_text(self) -> str:
        return get_notes('drops_notes.txt', self.gamestate.seed)

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

        output_data = []
        for event in self.gamestate.events_sequence:
            match event:
                case Comment() if event.text == '///':
                    output_data.clear()
                case _:
                    output_data.append(str(event))

        # update the text widget
        self.print_output('\n'.join(output_data))
