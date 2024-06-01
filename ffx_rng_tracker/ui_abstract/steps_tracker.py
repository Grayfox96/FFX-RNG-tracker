from ..data.encounters import get_steps_notes
from ..data.notes import save_notes
from ..events.parsing_functions import ParsingFunction, parse_encounter_checks
from ..ui_abstract.encounters_tracker import EncountersTracker


class StepsTracker(EncountersTracker):
    notes_file = 'steps_notes.csv'

    def get_parsing_functions(self) -> list[ParsingFunction]:
        parsing_functions = super().get_parsing_functions()
        parsing_functions.append(parse_encounter_checks)
        return parsing_functions

    def edit_output(self, output: str, padding: bool = False) -> str:
        output = (super().edit_output(output, False)
                  .replace('Encounters', '')
                  .replace(' steps before end of the zone', ''))
        output = ('Encounter checks: Zone (grace period) | # of Encounters'
                  f' | Trigger Steps | Steps before end of the Zone\n{output}'
                  )
        if padding:
            output = self.pad_output(output)
        output_lines = output.replace('Encounter checks: ', '').splitlines()
        output_lines.insert(1, '=' * len(output_lines[0]))
        return '\n'.join(output_lines)

    def save_input_data(self) -> None:
        seed = self.parser.gamestate.seed
        encounter_notes = get_steps_notes(self.notes_file, seed)
        current_input = (self.input_widget.get_input()
                         .replace('/nopadding\n', '')
                         .replace('///\n', '')
                         )
        current_input_lines = current_input.splitlines()
        notes_lines = []
        notes_lines.append(
            '#zone,label (optional),min,default,max,continue previous zone')
        for steps, line in zip(encounter_notes, current_input_lines):
            if line.startswith('Error: '):
                continue
            continue_previous_zone = str(steps.continue_previous_zone).lower()
            if steps.min == steps.max:
                notes_lines.append(f'{steps.zone},{steps.label},{steps.min},'
                                   f'{steps.default},{steps.max},'
                                   f'{continue_previous_zone}'
                                   )
                continue
            # steps event has syntax: walk {zone} {steps} {cpz}
            default = line.split()[2]
            notes_lines.append(f'{steps.zone},{steps.label},{steps.min},'
                               f'{default},{steps.max},'
                               f'{continue_previous_zone}'
                               )
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
