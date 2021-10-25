import csv
from dataclasses import dataclass, field
from typing import Dict

from .constants import Stat
from .file_functions import get_resource_path


@dataclass
class Character:
    name: str
    index: int
    _default_stats: Dict[str, int] = field(default_factory=dict)
    stats: Dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.reset_stats()

    def __str__(self):
        return self.name

    def set_stat(self, stat: Stat, value: int):
        value = min(max(value, 0), 255)
        self.stats[stat] = value

    def reset_stats(self):
        self.stats.clear()
        for stat, value in self._default_stats.items():
            self.set_stat(stat, value)


def _get_characters(file_path: str) -> Dict[str, Character]:
    """"""
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        file_reader = csv.reader(file_object, delimiter=',')
        # skips first line
        next(file_reader)
        characters = {}
        for line in file_reader:
            name = line[0]
            index = int(line[1])
            stats = {
                Stat.HP: int(line[2]),
                Stat.MP: int(line[3]),
                Stat.STRENGTH: int(line[4]),
                Stat.DEFENSE: int(line[5]),
                Stat.MAGIC: int(line[6]),
                Stat.MAGIC_DEFENSE: int(line[7]),
                Stat.AGILITY: int(line[8]),
                Stat.LUCK: int(line[9]),
                Stat.EVASION: int(line[10]),
                Stat.ACCURACY: int(line[11]),
                Stat.WEAPON_DAMAGE: int(line[12]),
                Stat.BONUS_CRIT: int(line[13]),
                Stat.BONUS_STRENGTH: int(line[14]),
                Stat.BONUS_MAGIC: int(line[15]),
                Stat.PIERCING: int(line[16])
            }
            characters[name.lower()] = Character(name, index, stats)
    return characters


CHARACTERS = _get_characters('data/characters.csv')
