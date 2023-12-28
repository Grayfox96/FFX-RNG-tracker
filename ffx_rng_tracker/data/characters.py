import json
from dataclasses import dataclass

from ..utils import open_cp1252
from .constants import Autoability, Character, EquipmentType, Stat
from .equipment import Equipment
from .file_functions import get_resource_path


@dataclass(frozen=True)
class DefaultCharacterState:
    character: Character
    index: int
    starting_s_lv: int
    stats: dict[Stat, int]
    weapon: Equipment
    armor: Equipment


def _get_characters(file_path: str) -> dict[Character, DefaultCharacterState]:
    """"""
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data: dict = json.load(file_object)
    characters = {}
    for character, character_data in data.items():
        character = Character(character)
        weapon_data = character_data['weapon']
        weapon = Equipment(
            owner=character,
            type_=EquipmentType.WEAPON,
            slots=weapon_data['slots'],
            abilities=[Autoability(a) for a in weapon_data['abilities']],
            base_weapon_damage=weapon_data['base_weapon_damage'],
            bonus_crit=weapon_data['bonus_crit'],
        )
        armor_data = character_data['armor']
        armor = Equipment(
            owner=character,
            type_=EquipmentType.ARMOR,
            slots=armor_data['slots'],
            abilities=[Autoability(a) for a in armor_data['abilities']],
            base_weapon_damage=16,
            bonus_crit=armor_data['bonus_crit'],
        )
        characters[character] = DefaultCharacterState(
            character=character,
            index=character_data['index'],
            starting_s_lv=character_data['starting_s_lv'],
            stats={Stat(k): v for k, v in character_data['stats'].items()},
            weapon=weapon,
            armor=armor,
        )

    return characters


def s_lv_to_ap(s_lv: int) -> int:
    """Returns the AP needed for a specific Sphere Level."""
    ap = int(5 * (s_lv + 1)) + int((s_lv ** 3) / 50)
    return min(ap, 22000)


def total_ap_to_s_lv(ap_total: int, starting_s_lv: int = 0) -> int:
    """Returns the Sphere Level reached with the given amount of AP."""
    ap = 0
    s_lv = 0
    while True:
        if ap_total < ap:
            return s_lv - 1
        ap += s_lv_to_ap(s_lv + starting_s_lv)
        s_lv += 1


def s_lv_to_total_ap(s_lv: int, starting_s_lv: int = 0) -> int:
    """Returns the AP needed to reach a specific Sphere Level."""
    return sum([s_lv_to_ap(i + starting_s_lv) for i in range(s_lv)])


def calculate_power_base(stats: dict[Stat, int]) -> int:
    power_base = ((min(stats[Stat.HP], 9999) // 100)
                  + (min(stats[Stat.MP], 999) // 10)
                  + stats[Stat.STRENGTH]
                  + stats[Stat.DEFENSE]
                  + stats[Stat.MAGIC]
                  + stats[Stat.MAGIC_DEFENSE]
                  + stats[Stat.AGILITY]
                  + stats[Stat.EVASION]
                  + stats[Stat.ACCURACY]
                  )
    return power_base


CHARACTERS_DEFAULTS = _get_characters('data_files/characters.json')
