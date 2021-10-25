import csv
from dataclasses import dataclass, field

from .constants import Stat
from .file_functions import get_resource_path


@dataclass
class Character:
    name: str
    index: int
    _default_stats: dict[Stat, int] = field(default_factory=dict)
    stats: dict[Stat, int] = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.reset_stats()

    def __str__(self):
        return self.name

    def set_stat(self, stat: Stat, value: int):
        if stat is Stat.HP:
            max_value = 99999
        elif stat is Stat.MP:
            max_value = 9999
        elif stat in (Stat.CHEER, Stat.FOCUS):
            max_value = 5
        elif stat is Stat.PIERCING:
            max_value = 1
        else:
            max_value = 255
        value = min(max(value, 0), max_value)
        self.stats[stat] = value

    def reset_stats(self):
        self.stats = self._default_stats.copy()


def _get_characters(file_path: str) -> dict[str, Character]:
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
                Stat.PIERCING: int(line[16]),
                Stat.CHEER: 0,
                Stat.FOCUS: 0,
            }
            characters[name.lower()] = Character(name, index, stats)
    return characters


CHARACTERS = _get_characters('data/characters.csv')
