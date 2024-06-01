from ..data.monsters import MONSTERS
from ..events.parsing_functions import (ParsingFunction, parse_bribe,
                                        parse_character_ap, parse_death,
                                        parse_inventory_command, parse_kill,
                                        parse_party_change, parse_roll,
                                        parse_steal)
from .base_tracker import TrackerUI


class DropsTracker(TrackerUI):
    notes_file = 'drops_notes.txt'

    def get_parsing_functions(self) -> list[ParsingFunction]:
        parsing_functions = [
            parse_roll,
            parse_party_change,
            parse_kill,
            parse_bribe,
            parse_steal,
            parse_death,
            parse_character_ap,
            parse_inventory_command,
        ]
        return parsing_functions

    def edit_input(self, input_text: str) -> str:
        input_lines = input_text.splitlines()
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case [monster, *_] if monster in MONSTERS:
                    line = f'kill {line}'
                case ['/usage']:
                    line = self.usage
                case _:
                    continue
            input_lines[index] = line
        return '\n'.join(input_lines)

    def get_paddings(self,
                     split_lines: list[list[str]]
                     ) -> dict[str, dict[int, int]]:
        paddings = super().get_paddings(split_lines)
        if 'Steal' in paddings and 'Drops' in paddings:
            padding = max(paddings['Steal'][0], paddings['Drops'][0])
            paddings['Steal'][0] = padding
            paddings['Drops'][0] = padding + 7
        return paddings

    def edit_output(self, output: str, padding: bool = False) -> str:
        # if the text contains /// it hides the lines before it
        if output.find('///') >= 0:
            output = output.split('///')[-1]
            output = output[output.find('\n') + 1:]
        if padding:
            output = self.pad_output(output)
        return output.replace('Drops: ', '')
