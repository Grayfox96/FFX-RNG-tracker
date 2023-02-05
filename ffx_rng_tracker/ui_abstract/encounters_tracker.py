from ..events.parsing_functions import (ParsingFunction, parse_encounter,
                                        parse_equipment_change, parse_roll)
from .base_tracker import TrackerUI


class EncountersTracker(TrackerUI):
    """Widget used to track encounters RNG."""

    def get_default_input_data(self) -> str:
        return ''

    def get_parsing_functions(self) -> dict[str, ParsingFunction]:
        parsing_functions = {
            'roll': parse_roll,
            'waste': parse_roll,
            'advance': parse_roll,
            'encounter': parse_encounter,
            'equip': parse_equipment_change,
        }
        return parsing_functions

    def edit_input(self, input_text: str) -> str:
        return input_text

    def edit_output(self, output: str) -> str:
        # if the text contains /// it hides the lines before it
        if output.find('///') >= 0:
            output = output.split('///')[-1]
            output = output[output.find('\n') + 1:]

        # remove implied information
        output = output.replace(' Normal', '')
        output = output.replace('Encounter ', '')

        output_lines = output.splitlines()
        for index, line in enumerate(output_lines):
            # remove information about initiative equipment
            if line.startswith('Tidus\'s Weapon'):
                output_lines[index] = ''
                continue
            # remove icvs
            if line.endswith(']') and '/' not in line:
                line = line.split('[')[0][:-3]
            # remove zone names
            # TODO
            # this method breaks if a zone name has a : character in it
            if '|' in line:
                dash_index = line.index('-') - 1
                colon_index = line.index(':', dash_index)
                line = line[:dash_index] + line[colon_index:]
            output_lines[index] = line

        # the condition removes empty lines
        output = '\n'.join([line for line in output_lines if line])

        return output
