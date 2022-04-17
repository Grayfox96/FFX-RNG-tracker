from ..data.monsters import MONSTERS
from ..data.notes import get_notes
from .base_tracker import TrackerUI


class DropsTracker(TrackerUI):

    def get_default_input_data(self) -> str:
        return get_notes(DROPS_NOTES_FILE, self.parser.gamestate.seed)

    def edit_input(self, input_text: str) -> str:
        input_lines = input_text.splitlines()
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case [monster, *params] if monster in MONSTERS:
                    line = ' '.join(['kill', monster, *params])
            input_lines[index] = line
        return '\n'.join(input_lines)

    def edit_output(self, output: str) -> str:
        if output.find('///') >= 0:
            output = output.split('///')[-1]
            output = output[output.find('\n') + 1:]
        return output


DROPS_NOTES_FILE = 'drops_notes.txt'
