from ..data.constants import Character
from ..data.monsters import MONSTERS
from ..events.parsing_functions import (ParsingFunction, parse_action,
                                        parse_encounter, parse_end_encounter,
                                        parse_equipment_change, parse_heal,
                                        parse_monster_action,
                                        parse_party_change, parse_roll,
                                        parse_stat_update, parse_summon)
from ..utils import stringify
from .base_tracker import TrackerUI


class ActionsTracker(TrackerUI):
    """Widget used to track damage, critical chance,
    escape chance and miss chance rng.
    """
    notes_file = 'actions_notes.txt'

    def get_parsing_functions(self) -> dict[str, ParsingFunction]:
        """Returns a dictionary with strings as keys
        and parsing functions as values.
        """
        parsing_functions = {
            'roll': parse_roll,
            'waste': parse_roll,
            'advance': parse_roll,
            'encounter': parse_encounter,
            'stat': parse_stat_update,
            'action': parse_action,
            'monsteraction': parse_monster_action,
            'party': parse_party_change,
            'summon': parse_summon,
            'equip': parse_equipment_change,
            'endencounter': parse_end_encounter,
            'heal': parse_heal,
        }
        return parsing_functions

    def edit_input(self, input_text: str) -> str:
        character_names = [stringify(c) for c in Character]
        input_lines = input_text.splitlines()
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case ['encounter', condition]:
                    if 'simulated'.startswith(condition):
                        name = 'simulation_(dummy)'
                    elif 'preemptive'.startswith(condition):
                        name = 'dummy_preemptive'
                    elif 'ambush'.startswith(condition):
                        name = 'dummy_ambush'
                    else:
                        continue
                    line = f'encounter {name}'
                case ['encounter']:
                    line = 'encounter dummy'
                case [character, *params] if character in character_names:
                    line = ' '.join(['action', character, *params])
                case [monster, *params] if monster in MONSTERS:
                    line = ' '.join(['monsteraction', monster, *params])
                case [monster, *params] if (monster.startswith('m')
                                            and monster[1:].isnumeric()):
                    line = ' '.join(['monsteraction', monster[1:], *params])
                case _:
                    continue
            input_lines[index] = line
        return '\n'.join(input_lines)

    def edit_output(self, output: str) -> str:
        # if the text contains /// it hides the lines before it
        if output.find('///') >= 0:
            output = output.split('///')[-1]
            output = output[output.find('\n') + 1:]
        output = output.replace(' - Simulation:  Normal', ': Simulation')
        output = output.replace(' - Boss: ', ':')
        output = output.replace('Normal ', '')
        return output
