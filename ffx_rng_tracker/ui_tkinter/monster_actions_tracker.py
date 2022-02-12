from ..data.file_functions import get_notes
from ..events.comment import Comment
from ..ui_functions import parse_monster_action, parse_party_change, parse_roll
from ..ui_tkinter.base_widgets import BaseWidget, BetterText


class MonsterActionsTracker(BaseWidget):

    def __init__(self, parent, *args, **kwargs) -> None:
        self.default_notes = get_notes('monster_actions_notes.txt')
        super().__init__(parent, *args, **kwargs)

    def make_input_widget(self) -> BetterText:
        widget = super().make_input_widget()
        widget.set(self.default_notes)
        return widget

    def get_input(self) -> None:
        self.rng_tracker.reset()
        input_lines = self.input_widget.get('1.0', 'end').split('\n')
        # parse through the input text
        for line in input_lines:
            match line.lower().split():
                case []:
                    event = Comment(line)
                case [*words] if words[0].startswith(('#', '///')):
                    event = Comment(line)
                case [('roll' | 'waste' | 'advance'), *params]:
                    event = parse_roll(*params)
                case ['party', *params]:
                    event = parse_party_change(*params)
                case [monster_name, *_]:
                    event = parse_monster_action(monster_name)

            self.rng_tracker.events_sequence.append(event)

    def get_tags(self) -> list[tuple[str, str, bool]]:
        tags = [
            ('^.*changed to.+$', 'stat update', True),
            ('^#(.+?)?$', 'comment', True),
        ]
        tags.extend(super().get_tags())
        return tags

    def print_output(self) -> None:
        self.get_input()
        data = []
        for event in self.rng_tracker.events_sequence:
            line = str(event)
            if '///' in line:
                data.clear()
            else:
                data.append(line)

        data = '\n'.join(data)

        self.output_widget.config(state='normal')
        self.output_widget.set(data)
        self.highlight_patterns()
        self.output_widget.config(state='disabled')
