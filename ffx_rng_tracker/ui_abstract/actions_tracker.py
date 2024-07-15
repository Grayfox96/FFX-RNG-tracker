from ..data.constants import Character
from ..data.monsters import get_monsters_dict
from ..events.parsing_functions import (
    ParsingFunction, parse_action, parse_actor_status, parse_encounter,
    parse_encounter_count_change, parse_end_encounter, parse_equipment_change,
    parse_heal, parse_monster_action,
    parse_monster_elemental_affinities_change, parse_monster_spawn,
    parse_party_change, parse_roll, parse_stat_update, parse_summon)
from ..utils import stringify
from .base_tracker import TrackerUI


class ActionsTracker(TrackerUI):
    """Widget used to track damage, critical chance,
    escape chance and miss chance rng.
    """
    notes_file = 'actions_notes.txt'

    def get_parsing_functions(self) -> list[ParsingFunction]:
        parsing_functions = [
            parse_roll,
            parse_encounter,
            parse_end_encounter,
            parse_encounter_count_change,
            parse_party_change,
            parse_summon,
            parse_equipment_change,
            parse_action,
            parse_monster_action,
            parse_heal,
            parse_actor_status,
            parse_monster_elemental_affinities_change,
            parse_monster_spawn,
            parse_stat_update,
        ]
        return parsing_functions

    def get_usage(self) -> str:
        usage = super().get_usage()
        usage += ('\n'
                  '# Stats:\n'
                  '#     hp, mp, strength, defense, magic,\n'
                  '#     magic_defense, agility, luck,\n'
                  '#     evasion, accuracy, ctb')
        return usage

    def edit_input(self, input_text: str) -> str:
        character_names = {stringify(c) for c in Character}
        monster_names = (set(get_monsters_dict())
                         | {f'm{i + 1}' for i in range(8)}
                         )
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
                case [character, *_] if character in character_names:
                    line = f'action {line}'
                case [monster, *_] if monster in monster_names:
                    line = f'monsteraction {line}'
                case [equip_type, *_] if equip_type in ('weapon', 'armor'):
                    line = f'equip {line}'
                case ['/usage']:
                    line = self.usage
                case _:
                    continue
            input_lines[index] = line
        return '\n'.join(input_lines)

    def edit_output(self, output: str, padding: bool = False) -> str:
        # if the text contains /// it hides the lines before it
        if output.find('Command: ///') >= 0:
            output = output.split('Command: ///')[-1]
            output = output[output.find('\n') + 1:]
        output = (output
                  .replace('Boss', '')
                  .replace(' Normal', '')
                  .replace('Random ', '')
                  .replace('Simulated ', '')
                  )
        if padding:
            output = self.pad_output(output)
        return output
