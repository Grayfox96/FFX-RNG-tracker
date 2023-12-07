from ..data.encounter_formations import ZONES
from ..data.encounters import get_steps_notes
from ..data.notes import save_notes
from ..events.parsing_functions import ParsingFunction, parse_encounter_checks
from ..ui_abstract.encounters_tracker import EncountersTracker


class StepsTracker(EncountersTracker):
    notes_file = 'steps_notes.csv'

    def get_parsing_functions(self) -> dict[str, ParsingFunction]:
        parsing_functions = super().get_parsing_functions()
        parsing_functions['walk'] = parse_encounter_checks
        return parsing_functions

    def edit_output(self, output: str) -> str:
        output = super().edit_output(output)
        for zone in ZONES.values():
            output = output.replace(f'{zone}: ', '')
        return output

    def save_input_data(self) -> None:
        seed = self.parser.gamestate.seed
        encounter_notes = get_steps_notes(self.notes_file, seed)
        current_input_lines = self.input_widget.get_input().splitlines()
        notes_lines = []
        notes_lines.append(
            '#zone,label (optional),min,default,max,continue previous zone')
        for steps in encounter_notes:
            continue_previous_zone = str(steps.continue_previous_zone).lower()
            if steps.min == steps.max:
                notes_lines.append(f'{steps.zone},{steps.label},{steps.min},'
                                   f'{steps.default},{steps.max},'
                                   f'{continue_previous_zone}'
                                   )
                continue
            # find which line corresponds with the label
            for input_index, input_line in enumerate(current_input_lines):
                if input_line.startswith(f'# {steps.label} ('):
                    break
            else:
                continue
            # steps event has syntax: walk {zone} {steps} {cpz}
            default = current_input_lines[input_index + 1].split()[2]
            notes_lines.append(f'{steps.zone},{steps.label},{steps.min},'
                               f'{default},{steps.max},'
                               f'{continue_previous_zone}'
                               )
        notes = '\n'.join(notes_lines)
        try:
            save_notes(self.notes_file, seed, notes)
        except FileExistsError as error:
            self.confirmation_popup.print_output(
                f'Do you want to overwrite file {error.args[0]!r}?')
            if self.confirmation_popup.confirmed:
                save_notes(self.notes_file, seed, notes, force=True)
                self.warning_popup.print_output(
                    f'File "{seed}_{self.notes_file}" '
                    'saved successfully!')
        else:
            self.warning_popup.print_output(
                f'File "{seed}_{self.notes_file}" saved successfully!')
