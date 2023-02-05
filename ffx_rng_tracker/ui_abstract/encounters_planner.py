import re
from dataclasses import dataclass

from ..data.monsters import MONSTERS
from .encounters_tracker import EncountersTracker
from .input_widget import InputWidget


@dataclass
class EncountersPlanner(EncountersTracker):
    search_bar: InputWidget

    def edit_output(self, output: str) -> str:
        output = output.replace('Simulation: ', 'Simulation')
        output = output.replace('Boss: ', 'Boss')
        # TODO
        # find a way to find conflicting monster names
        # instead of hardcoding them
        conflicting_monster_names = (
            'Chimera Brain', 'Master Coeurl', 'Master Tonberry',
            'Great Malboro', 'Behemoth King', 'Gemini#3',
            )
        for name in conflicting_monster_names:
            output = output.replace(name, name.upper())

        monsters_tally = {}
        for monster in MONSTERS.values():
            name = monster.name
            if name in conflicting_monster_names:
                name = name.upper()
            index = 0
            while True:
                try:
                    index_1 = output.index(f', {name}', index)
                except ValueError:
                    index_1 = len(output) + 1
                try:
                    index_2 = output.index(f': {name}', index)
                except ValueError:
                    index_2 = len(output) + 1
                index = min(index_1, index_2)
                if index > len(output):
                    break
                tally = monsters_tally.get(name, 0) + 1
                monsters_tally[name] = tally
                index += len(name) + 2
                output = f'{output[:index]}{{{tally}}}{output[index:]}'

        captured_monsters = [re.escape(m)
                             for m, t in monsters_tally.items()
                             if t >= 10]
        pattern = '|'.join(captured_monsters)
        self.output_widget.regex_patterns['captured monster'] = pattern

        important_monsters = self.search_bar.get_input()
        for symbol in (',', '-', '/', '\\', '.'):
            important_monsters = important_monsters.replace(symbol, ' ')
        important_monsters = important_monsters.split()
        pattern = '|'.join([re.escape(m.strip()) for m in important_monsters])
        self.output_widget.regex_patterns['important monster'] = pattern

        return super().edit_output(output)
