
from ..data.encounter_formations import ZONES
from ..events.parsing_functions import ParsingFunction, parse_encounter_checks
from ..ui_abstract.encounters_tracker import EncountersTracker


class StepsTracker(EncountersTracker):

    def get_parsing_functions(self) -> dict[str, ParsingFunction]:
        parsing_functions = super().get_parsing_functions()
        parsing_functions['walk'] = parse_encounter_checks
        return parsing_functions

    def edit_output(self, output: str) -> str:
        output = super().edit_output(output)
        for zone in ZONES.values():
            output = output.replace(f'{zone}: ', '')
        return output
