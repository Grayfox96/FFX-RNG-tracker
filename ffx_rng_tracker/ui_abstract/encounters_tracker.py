from ..data.encounters import get_encounter_notes
from ..data.notes import save_notes
from ..events.parsing_functions import (ParsingFunction, parse_encounter,
                                        parse_encounter_count_change,
                                        parse_equipment_change, parse_roll)
from .base_tracker import TrackerUI


class EncountersTracker(TrackerUI):
    """Widget used to track encounters RNG."""
    notes_file = 'encounters_notes.csv'

    def get_default_input_data(self) -> str:
        encounters = get_encounter_notes(
            self.notes_file, self.parser.gamestate.seed)
        lines = ['/nopadding', '/usage']
        initiative_equipped = False
        for encounter in encounters:
            if encounter.initiative and not initiative_equipped:
                lines.append('weapon tidus 1 initiative')
                initiative_equipped = True
            elif not encounter.initiative and initiative_equipped:
                lines.append('weapon tidus 1')
                initiative_equipped = False

            if ' ' in encounter.name:
                multizone = 'multizone '
            else:
                multizone = ''
            line = f'encounter {multizone}{encounter.name}'
            if encounter.min == encounter.max:
                lines.extend([line] * encounter.default)
                continue

            lines.append(f'\n#    {encounter.label}')
            lines.extend([line] * encounter.default)
            lines.extend([f'# {line}'] * (encounter.max - encounter.default))
        return '\n'.join(lines).strip('\n')

    def get_parsing_functions(self) -> list[ParsingFunction]:
        parsing_functions = [
            parse_roll,
            parse_encounter,
            parse_equipment_change,
            parse_encounter_count_change,
        ]
        return parsing_functions

    def edit_input(self, input_text: str) -> str:
        return input_text

    def edit_output(self, output: str, padding: bool = False) -> str:
        # if the text contains /// it hides the lines before it
        if output.find('Command: ///') >= 0:
            output = output.split('Command: ///')[-1]
            output = output[output.find('\n') + 1:]

        output_lines = output.splitlines()
        for index, line in enumerate(output_lines):
            # remove information about initiative equipment
            if line.startswith('Equipment:') or line.startswith('Command:'):
                output_lines[index] = ''
                continue

            if (line.startswith('Random Encounter:')
                    or line.startswith('Simulated Encounter:')):
                parts = line.split('|')
                # remove zone name
                parts.pop(1)
                # remove icvs
                parts.pop()
                line = '|'.join(parts)
            elif line.startswith('Encounter:'):
                parts = line.split('|')
                # remove icvs
                parts.pop()
                line = '|'.join(parts)
            output_lines[index] = line

        # the condition removes empty lines
        output = '\n'.join([line for line in output_lines if line])
        if not output:
            return output
        output = (output
                  .replace(' Normal', '')
                  .replace('Random Encounter:', 'Encounter:')
                  .replace('Simulated Encounter:', 'Encounter:')
                  .replace('| -', '')
                  )
        if padding:
            output = self.pad_output(output)
        output = output.replace('Encounter: ', '')
        output_lines = output.splitlines()
        output = '\n'.join(output_lines)
        spacer = f'{'=' * max(len(line) for line in output_lines)}\n'
        index = 0
        while (index := output.find('\n#    ', index)) >= 0:
            output = output[:index + 1] + spacer + output[index + 1:]
            index += len(spacer) + 2
        return output

    def save_input_data(self) -> None:
        seed = self.parser.gamestate.seed
        encounter_notes = get_encounter_notes(self.notes_file, seed)
        current_input_lines = self.input_widget.get_input().splitlines()
        notes_lines = []
        notes_lines.append('#name or zone,initiative (true or false),'
                           'label (optional),min,default,max')
        labels_tally: dict[str, int] = {}
        for enc in encounter_notes:
            initiative = str(enc.initiative).lower()
            if enc.min == enc.max:
                notes_lines.append(f'{enc.name},{initiative},{enc.label},'
                                   f'{enc.min},{enc.default},{enc.max}')
                continue
            # find which line corresponds with the label, label might not
            # be unique, find out how many were already processed
            label = f'#     {enc.label}:'
            count = current_input_lines.count(label)
            if count == 1:
                input_index = current_input_lines.index(label)
            else:
                already_used = labels_tally.get(label, 0)
                labels_tally[label] = already_used + 1
                input_index = -1
                for _ in range(already_used + 1):
                    input_index = current_input_lines.index(label, input_index + 1)
            # if zone has a space it must be a multizone random encounter
            if ' ' in enc.name:
                multizone = 'multizone '
            else:
                multizone = ''
            encounter_line = f'encounter {multizone}{enc.name}'
            # start counting encounters from the line after the label
            default = 0
            for input_line in current_input_lines[input_index + 1:]:
                if input_line != encounter_line:
                    break
                default += 1
            notes_lines.append(f'{enc.name},{initiative},{enc.label},'
                               f'{enc.min},{default},{enc.max}')
        notes = '\n'.join(notes_lines)
        try:
            save_notes(self.notes_file, seed, notes)
        except FileExistsError as error:
            confirmed = self.confirmation_popup.print_output(
                f'Do you want to overwrite file {error.args[0]!r}?')
            if confirmed:
                save_notes(self.notes_file, seed, notes, force=True)
                self.warning_popup.print_output(
                    f'File "{seed}_{self.notes_file}" '
                    'saved successfully!')
        else:
            self.warning_popup.print_output(
                f'File "{seed}_{self.notes_file}" saved successfully!')
