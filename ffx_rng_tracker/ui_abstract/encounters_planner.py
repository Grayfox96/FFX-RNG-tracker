import re
from dataclasses import dataclass

from ..configs import REGEX_NEVER_MATCH, UITagConfigs
from ..data.monsters import get_monsters_dict
from .encounters_tracker import EncountersTracker


@dataclass
class EncountersPlanner(EncountersTracker):

    def __post_init__(self) -> None:
        super().__post_init__()
        self.output_widget.register_tag(
            '#captured monsters',
            UITagConfigs(REGEX_NEVER_MATCH, foreground='#cccccc'),
            )

    def get_default_input_data(self) -> str:
        return ''

    def edit_output(self, output: str, padding: bool = False) -> str:
        output = output.replace('Simulated ', '')
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
        for monster in get_monsters_dict().values():
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
                    index_2 = output.index(f'| {name}', index)
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
        tag = self.output_widget.tags['#captured monsters']
        if captured_monsters:
            pattern = '|'.join(captured_monsters)
            tag.regex_pattern = re.compile(pattern, flags=re.IGNORECASE)
        else:
            tag.regex_pattern = REGEX_NEVER_MATCH
        return super().edit_output(output, padding)

    def search_callback(self) -> None:
        search = self.search_bar.get_input()
        self.output_widget.seek(search)
        for symbol in (',', '-', '/', '\\', '.'):
            search = search.replace(symbol, ' ')
        words = search.split()
        tag = self.output_widget.tags['#search bar']
        self.output_widget.clean_tag('#search bar')
        if not words:
            tag.regex_pattern = REGEX_NEVER_MATCH
            return
        pattern = '|'.join([re.escape(w) for w in words])
        tag.regex_pattern = re.compile(pattern, flags=re.IGNORECASE)
        self.output_widget.highlight_pattern('#search bar', tag.regex_pattern)
