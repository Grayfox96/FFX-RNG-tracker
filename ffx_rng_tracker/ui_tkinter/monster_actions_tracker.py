from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.parsing import (parse_monster_action, parse_party_change,
                              parse_roll)
from ..ui_tkinter.base_widgets import BaseWidget


class MonsterActionsTracker(BaseWidget):

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            ('^.*changed to.+$', 'stat update', True),
            ('^#(.+?)?$', 'comment', True),
        ]
        tags.extend(super().get_tags())
        return tags

    def get_default_input_text(self) -> str:
        return get_notes('monster_actions_notes.txt', self.gamestate.seed)

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
                case ['party', *params]:
                    event = parse_party_change(gs, *params)
                case [monster_name, *_]:
                    event = parse_monster_action(gs, monster_name)

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
