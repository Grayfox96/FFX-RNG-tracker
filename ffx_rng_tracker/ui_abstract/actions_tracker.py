from ..data.constants import Character
from ..data.monsters import MONSTERS
from ..events.parsing_functions import (ParsingFunction, parse_action,
                                        parse_character_status,
                                        parse_encounter, parse_end_encounter,
                                        parse_equipment_change, parse_heal,
                                        parse_monster_action,
                                        parse_monster_spawn,
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
            'status': parse_character_status,
            'spawn': parse_monster_spawn,
        }
        return parsing_functions

    def edit_input(self, input_text: str) -> str:
        character_names = [stringify(c) for c in Character]
        input_lines = input_text.splitlines()
        for index, line in enumerate(input_lines):
            match line.lower().split():
                case ['encounter', condition]:
                    if 'simulated'.startswith(condition):
                        name = 'simulation'
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
                    line = ' '.join(['monsteraction', monster, *params])
                case [equip_type, *params] if equip_type in ('weapon', 'armor'):
                    line = ' '.join(['equip', equip_type, *params])
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
