from ..data.monsters import MONSTERS
from ..data.notes import get_notes
from ..events.parsing_functions import (ParsingFunction, parse_bribe,
                                        parse_death, parse_kill,
                                        parse_party_change, parse_steal)
from .base_widgets import BaseTracker


class DropsTracker(BaseTracker):
    """Widget used to track monster drops RNG."""

    def get_tags(self) -> dict[str, str]:
        tags = {
            'equipment': 'Equipment',
            'no encounters': 'No Encounters',
            'stat update': '^.*changed to.+$',
        }
        tags.update(super().get_tags())
        return tags

    def get_parsing_functions(self) -> dict[str, ParsingFunction]:
        parsing_functions = super().get_parsing_functions()
        parsing_functions['steal'] = parse_steal
        parsing_functions['kill'] = parse_kill
        parsing_functions['death'] = parse_death
        parsing_functions['party'] = parse_party_change
        parsing_functions['bribe'] = parse_bribe
        return parsing_functions

    def get_default_input_text(self) -> str:
        return get_notes('drops_notes.txt', self.gamestate.seed)

    def get_input(self) -> str:
        input_data = super().get_input()
        input_lines = input_data.split('\n')
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case [monster, *params] if monster in MONSTERS:
                    line = ' '.join(['kill', monster, *params])
            input_lines[index] = line
        return '\n'.join(input_lines)

    def parse_input(self) -> None:
        self.gamestate.reset()
        events_sequence = self.parser.parse(self.get_input())
        data = '\n'.join(str(e) for e in events_sequence)
        # if the text contains /// it hides the lines before it
        if data.find('///') >= 0:
            data = data.split('///')[-1]
            data = data[data.find('\n') + 1:]

        # update the text widget
        self.print_output(data)
