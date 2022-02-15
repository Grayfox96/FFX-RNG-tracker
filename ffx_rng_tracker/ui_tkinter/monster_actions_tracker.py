from ..data.notes import get_notes
from ..events.comment import Comment
from ..events.parsing import (parse_monster_action, parse_party_change,
                              parse_roll)
from ..ui_tkinter.base_widgets import BaseWidget, BetterText


class MonsterActionsTracker(BaseWidget):

    def make_input_widget(self) -> BetterText:
        widget = super().make_input_widget()
        notes = get_notes('monster_actions_notes.txt', self.gamestate.seed)
        widget.set(notes)
        return widget

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            ('^.*changed to.+$', 'stat update', True),
            ('^#(.+?)?$', 'comment', True),
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
                case ['party', *params]:
                    event = parse_party_change(gs, *params)
                case [monster_name, *_]:
                    event = parse_monster_action(gs, monster_name)

            self.gamestate.events_sequence.append(event)

    def print_output(self) -> None:
        self.get_input()
        data = []
        for event in self.gamestate.events_sequence:
            match event:
                case Comment() if '///' in event.text:
                    data.clear()
                case _:
                    data.append(str(event))

        self.output_widget.config(state='normal')
        self.output_widget.set('\n'.join(data))
        self.highlight_patterns()
        self.output_widget.config(state='disabled')
