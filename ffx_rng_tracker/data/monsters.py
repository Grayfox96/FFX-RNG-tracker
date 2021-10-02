import csv
import sys
from dataclasses import dataclass
from typing import Optional, Union

from .autoabilities import AUTOABILITIES
from .characters import CHARACTERS, Character
from .constants import (Element, ElementalAffinity, EquipmentSlots,
                        EquipmentType, Rarity, Stat, Status)
from .file_functions import get_resource_path
from .items import ITEMS, ItemDrop
from .text_characters import TEXT_CHARACTERS


@dataclass
class Monster:
    name: str
    stats: dict[Stat, int]
    elemental_affinities: dict[Element, ElementalAffinity]
    status_resistances: dict[Status, int]
    zanmato_level: int
    armored: bool
    undead: bool
    auto_statuses: list[Status]
    gil: int
    ap: dict[str, int]
    item_1: dict[str, Union[int, dict[Rarity, Optional[ItemDrop]]]]
    item_2: dict[str, Union[int, dict[Rarity, Optional[ItemDrop]]]]
    steal: dict[Union[str, Rarity], Union[int, Optional[ItemDrop]]]
    bribe: dict[Union[str, Rarity], Union[int, Optional[ItemDrop]]]
    equipment: dict[str, Union[int, list, dict[Character, list[int]]]]

    def __str__(self):
        return self.name


def _get_prize_structs(file_path: str) -> dict[str, list[int]]:
    """Retrieves the prize structs for enemies."""
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        file_reader = csv.reader(file_object, delimiter=',')
        # skips first line
        next(file_reader)
        monsters_data = {}

        for line in file_reader:
            prize_struct = [int(value, 16) for value in line]
            # gets the name of the monster from the prize struct itself
            # name is null (0x00) terminated
            monster_name = ''
            for i in range(408, 430):
                if prize_struct[i] == 0:
                    break
                monster_name += TEXT_CHARACTERS[prize_struct[i]]
            monster_name = monster_name.lower().replace(' ', '_')
            # if the name is already in the dictionary
            # appends it with an underscore and a number
            # from 2 to 8
            if monster_name in monsters_data:
                for i in range(2, 9):
                    new_name = f'{monster_name}_{i}'
                    if new_name not in monsters_data:
                        monsters_data[new_name] = prize_struct
                        break
            else:
                monsters_data[monster_name] = prize_struct
    return monsters_data


def _patch_prize_structs_for_hd(
        prize_structs: dict[str, list[int]]) -> dict[str, list[int]]:
    """Apply changes made in the HD version to the prize structs."""
    def patch_abilities(
            monster_name: str,
            abilities: tuple[int, int, int, int, int, int, int],
            equipment_type: EquipmentType = EquipmentType.WEAPON) -> None:
        """Modifies ability values 1-7 of every character's weapon
        or armor ability array.
        """
        # base address for abilities in the prize struct
        base_address = 178
        type_offset = 0 if equipment_type == EquipmentType.WEAPON else 1
        # place the abilities values at the correct offsets
        for owner_index in range(7):
            offset = (type_offset + (owner_index * 2)) * 16
            for slot in range(7):
                slot_offset = (slot + 1) * 2
                address = base_address + offset + slot_offset
                prize_structs[monster_name][address] = abilities[slot]

    # in the HD version equipment droprates were modified
    # from 8/255 to 12/255 for these enemies
    monster_names = (
        'condor', 'dingo', 'water_flan', 'condor_2', 'dingo_2',
        'water_flan_2', 'dinonix', 'killer_bee', 'yellow_element',
        'worker', 'vouivre_2', 'raldo_2', 'floating_eye', 'ipiria',
        'mi\'ihen_fang', 'raldo', 'vouivre', 'white_element', 'funguar',
        'gandarewa', 'lamashtu', 'raptor', 'red_element', 'thunder_flan',
        'bite_bug', 'bunyip', 'garm', 'simurgh', 'snow_flan', 'bunyip_2',
        'aerouge', 'buer', 'gold_element', 'kusariqqu', 'melusine',
        'blue_element', 'iguion', 'murussu', 'wasp', 'evil_eye',
        'ice_flan', 'mafdet', 'snow_wolf', 'guado_guardian_2', 'alcyone',
        'mech_guard', 'mushussu', 'sand_wolf', 'bomb_2', 'evil_eye_2',
        'guado_guardian_3', 'warrior_monk', 'warrior_monk_2', 'aqua_flan',
        'bat_eye', 'cave_iguion', 'sahagin_2', 'swamp_mafdet',
        'sahagin_3', 'flame_flan', 'mech_scouter', 'mech_scouter_2',
        'nebiros', 'shred', 'skoll', 'flame_flan', 'nebiros', 'shred',
        'skoll', 'dark_element', 'imp', 'nidhogg', 'yowie',
    )
    for monster_name in monster_names:
        prize_structs[monster_name][139] = 12

    # all the enemies that have ability arrays modified in the HD version
    # besaid
    patch_abilities('dingo', (38, 42, 34, 30, 124, 124, 124))
    patch_abilities('condor', (0, 0, 0, 0, 126, 126, 126))
    patch_abilities('water_flan', (42, 42, 42, 42, 125, 125, 125))
    patch_abilities('dingo_2', (38, 42, 34, 30, 124, 124, 124))
    patch_abilities('condor_2', (0, 0, 0, 0, 126, 126, 126))
    patch_abilities('water_flan_2', (42, 42, 42, 42, 125, 125, 125))

    # kilika
    patch_abilities('dinonix', (38, 42, 38, 30, 126, 126, 126))
    patch_abilities('killer_bee', (38, 42, 34, 30, 126, 126, 126))
    patch_abilities('yellow_element', (38, 38, 38, 38, 125, 125, 125))

    # luca
    patch_abilities('vouivre_2', (38, 42, 34, 30, 124, 124, 124))

    # mi'ihen
    patch_abilities('raldo_2', (38, 42, 34, 30, 124, 124, 124))
    # bomb
    # dual_horn
    # floating_eye
    # ipiria
    # mi'ihen_fang
    patch_abilities('raldo', (38, 42, 34, 30, 124, 124, 124))
    patch_abilities('vouivre', (38, 42, 34, 30, 124, 124, 124))
    # white_element

    # mushroom rock road
    # patch_abilities('gandarewa', (38, 38, 38, 38, 125, 125, 125))
    # patch_abilities('lamashtu', (124, 124, 124, 30, 34, 38, 42))
    # patch_abilities('raptor', (126, 126, 126, 38, 38, 30, 42))
    # patch_abilities('red_element', (30, 30, 30, 30, 125, 125, 125))
    # patch_abilities('thunder_flan', (38, 38, 38, 38, 125, 125, 125))

    # djose highroad
    # bite_bug
    # patch_abilities('bunyip', (124, 124, 124, 30, 34, 38, 42))
    # garm
    # simurgh
    # snow_flan

    # moonflow
    # patch_abilities('bunyip_2', (124, 124, 124, 30, 34, 38, 42))

    # thunder plains
    # aerouge
    # patch_abilities('buer', (126, 126, 30, 34, 38, 42, 99))
    # gold_element
    # kusariqqu
    # melusine

    # macalania woods
    # blue_element
    # chimera
    # iguion
    # murussu
    # wasp

    # lake macalania
    # patch_abilities('evil_eye', (126, 126, 30, 34, 38, 42, 99))
    # patch_abilities('ice_flan', (34, 34, 34, 34, 125, 125, 125))
    # patch_abilities('mafdet', (124, 124, 124, 30, 34, 38, 42))
    # patch_abilities('snow_wolf', (124, 124, 124, 30, 34, 38, 42))

    # bikanel
    # patch_abilities('alcyone', (0, 0, 0, 0, 126, 126, 126))
    # patch_abilities('mushussu', (124, 124, 124, 30, 34, 38, 42))
    # patch_abilities('sand_wolf', (124, 124, 124, 30, 34, 38, 42))

    # patch_abilities('bomb_2', (30, 30, 30, 30, 30, 30, 124))
    # patch_abilities('chimera_2', (103, 103, 103, 103, 104, 104, 125))
    # patch_abilities('dual_horn_2', (67, 67, 67, 30, 30, 127, 127))
    # patch_abilities('evil_eye_2', (126, 126, 30, 34, 38, 42, 99))

    # via purifico
    # aqua_flan
    # bat_eye
    # cave_iguion
    # swamp_mafdet

    # calm lands
    # chimera_brain
    # flame_flan
    # nebiros
    # shred
    # skoll
    # patch_abilities('defender_x', (99, 99, 99, 99, 99, 100, 124))

    # cavern of the stolen fayth
    # patch_abilities('dark_element', (125, 125, 125, 30, 30, 34, 42))
    # patch_abilities('defender', (99, 99, 99, 99, 98, 98, 124))
    # patch_abilities('ghost', (103, 103, 103, 104, 104, 104, 125))
    # patch_abilities('imp', (38, 38, 38, 38, 125, 125, 125))
    # patch_abilities('nidhogg', (124, 124, 124, 30, 34, 38, 42))
    # patch_abilities('valaha', (67, 67, 67, 30, 30, 127, 127))
    # patch_abilities('yowie', (126, 126, 126, 38, 38, 30, 42))
    return prize_structs


def get_raw_data_string(prize_struct: list[str]) -> str:
    string = ''
    for index, byte in enumerate(prize_struct):
        # every 16 bytes make a new line
        if index % 16 == 0:
            string += '\n'
            string += ' '.join(
                [f'[{hex(index + i)[2:]:>3}]' for i in range(16)])
            string += '\n'
        # print the bytes' value
        # string += f' {hex(byte)[2:]:>3}  '
        string += f' {byte:>3}  '
        # string += f' {byte:08b}  '
    return string


def _get_monster_data(
        internal_monster_name: str, prize_struct: list[int]) -> Monster:
    """Get a Monster from his prize struct."""
    def add_bytes(address: int, length: int) -> int:
        """Adds the value of adjacent bytes in a prize struct."""
        value = 0
        for i in range(length):
            value += prize_struct[address + i] * (256 ** i)
        return value

    def get_elements() -> dict[str, str]:
        elements = {
            Element.FIRE: 0b00001,
            Element.ICE: 0b00010,
            Element.THUNDER: 0b00100,
            Element.WATER: 0b01000,
            Element.HOLY: 0b10000,
        }
        affinities = {}
        for element, value in elements.items():
            if prize_struct[43] & value:
                affinities[element] = ElementalAffinity.ABSORBS
            elif prize_struct[44] & value:
                affinities[element] = ElementalAffinity.IMMUNE
            elif prize_struct[45] & value:
                affinities[element] = ElementalAffinity.HALVES
            elif prize_struct[46] & value:
                affinities[element] = ElementalAffinity.WEAK
            else:
                affinities[element] = ElementalAffinity.NEUTRAL
        return affinities

    def get_abilities(address: int) -> dict[str, list[Optional[str]]]:
        abilities = {}
        equipment_types = (EquipmentType.WEAPON, 0), (EquipmentType.ARMOR, 16)
        for equipment_type, offset in equipment_types:
            abilities[equipment_type] = []
            for i in range(address + offset, address + 16 + offset, 2):
                if prize_struct[i + 1] == 128:
                    ability_name = AUTOABILITIES[prize_struct[i]]
                else:
                    ability_name = None
                abilities[equipment_type].append(ability_name)
        return abilities

    monster_name = ''
    for i in range(408, 430):
        if prize_struct[i] == 0:
            break
        monster_name += TEXT_CHARACTERS[prize_struct[i]]
    for i in range(8):
        if internal_monster_name.endswith(f'_{i}'):
            if '-nounicode' in sys.argv:
                monster_name += f'#{i}'
            else:
                # ① ② ③ ④ ⑤ ⑥ ⑦ ⑧ ⑨ ⑩ ⑪ ⑫ ⑬ ⑭ ⑮ ⑯
                monster_name += chr(9311 + i)
            break

    stats = {
        Stat.HP: add_bytes(20, 4),
        Stat.MP: add_bytes(24, 4),
        'overkill_threshold': add_bytes(28, 4),
        Stat.STRENGTH: prize_struct[32],
        Stat.DEFENSE: prize_struct[33],
        Stat.MAGIC: prize_struct[34],
        Stat.MAGIC_DEFENSE: prize_struct[35],
        Stat.AGILITY: prize_struct[36],
        Stat.LUCK: prize_struct[37],
        Stat.EVASION: prize_struct[38],
        Stat.ACCURACY: prize_struct[39],
    }

    gil = add_bytes(128, 2)
    ap = {'normal': add_bytes(130, 2), 'overkill': add_bytes(132, 2)}
    item_1 = {
        'drop_chance': prize_struct[136],
        'normal': {Rarity.COMMON: None, Rarity.RARE: None},
        'overkill': {Rarity.COMMON: None, Rarity.RARE: None},
    }
    if prize_struct[141] == 32:
        item_1['normal'][Rarity.COMMON] = ItemDrop(
            ITEMS[prize_struct[140]], prize_struct[148], False)
    if prize_struct[143] == 32:
        item_1['normal'][Rarity.RARE] = ItemDrop(
            ITEMS[prize_struct[142]], prize_struct[149], True)
    if prize_struct[153] == 32:
        item_1['overkill'][Rarity.COMMON] = ItemDrop(
            ITEMS[prize_struct[152]], prize_struct[160], False)
    if prize_struct[155] == 32:
        item_1['overkill'][Rarity.RARE] = ItemDrop(
            ITEMS[prize_struct[154]], prize_struct[161], True)

    item_2 = {
        'drop_chance': prize_struct[137],
        'normal': {Rarity.COMMON: None, Rarity.RARE: None},
        'overkill': {Rarity.COMMON: None, Rarity.RARE: None},
    }
    if prize_struct[145] == 32:
        item_2['normal'][Rarity.COMMON] = ItemDrop(
            ITEMS[prize_struct[144]], prize_struct[150], False)
    if prize_struct[147] == 32:
        item_2['normal'][Rarity.RARE] = ItemDrop(
            ITEMS[prize_struct[146]], prize_struct[151], True)
    if prize_struct[157] == 32:
        item_2['overkill'][Rarity.COMMON] = ItemDrop(
            ITEMS[prize_struct[156]], prize_struct[162], False)
    if prize_struct[159] == 32:
        item_2['overkill'][Rarity.RARE] = ItemDrop(
            ITEMS[prize_struct[158]], prize_struct[163], True)

    steal = {
        'base_chance': prize_struct[138],
        Rarity.COMMON: None,
        Rarity.RARE: None,
    }
    if prize_struct[165] == 32:
        steal[Rarity.COMMON] = ItemDrop(
            ITEMS[prize_struct[164]], prize_struct[168], False)
    if prize_struct[167] == 32:
        steal[Rarity.RARE] = ItemDrop(
            ITEMS[prize_struct[166]], prize_struct[169], True)
    bribe = {
        'cost': float('nan'),
        'item': None,
    }
    if prize_struct[171] == 32:
        bribe['item'] = ItemDrop(
            ITEMS[prize_struct[170]], prize_struct[172], False)

    elemental_affinities = get_elements()

    status_resistances = {
        Status.DEATH: prize_struct[47],
        Status.ZOMBIE: prize_struct[48],
        Status.PETRIFY: prize_struct[49],
        Status.POISON: prize_struct[50],
        Status.POWER_BREAK: prize_struct[51],
        Status.MAGIC_BREAK: prize_struct[52],
        Status.ARMOR_BREAK: prize_struct[53],
        Status.MENTAL_BREAK: prize_struct[54],
        Status.CONFUSE: prize_struct[55],
        Status.BERSERK: prize_struct[56],
        Status.PROVOKE: prize_struct[57],
        Status.THREATEN: prize_struct[58],
        Status.SLEEP: prize_struct[59],
        Status.SILENCE: prize_struct[60],
        Status.DARK: prize_struct[61],
        Status.PROTECT: prize_struct[62],
        Status.SHELL: prize_struct[63],
        Status.REFLECT: prize_struct[64],
        Status.NULBLAZE: prize_struct[65],
        Status.NULFROST: prize_struct[66],
        Status.NULSHOCK: prize_struct[67],
        Status.NULTIDE: prize_struct[68],
        Status.REGEN: prize_struct[69],
        Status.HASTE: prize_struct[70],
        Status.SLOW: prize_struct[71],
    }
    undead = prize_struct[72] == 2
    auto_statuses = []
    if prize_struct[74] & 0b00100000:
        auto_statuses.append(Status.REFLECT)
    if (prize_struct[75] & 0b00000011
            and prize_struct[74] & 0b11000000):
        auto_statuses.append(Status.NULALL)
    if prize_struct[75] & 0b00000100:
        auto_statuses.append(Status.REGEN)

    equipment = {
        'drop_chance': prize_struct[139],
        'bonus_critical_chance': prize_struct[175],
        'base_weapon_damage': prize_struct[176],
        'slots_modifier': prize_struct[173],
        'slots_range': [],
        'max_ability_rolls_modifier': prize_struct[177],
        'max_ability_rolls_range': [],
        'added_to_inventory': bool(prize_struct[174]),
    }

    for i in range(8):
        slots_mod = equipment['slots_modifier'] + i - 4
        slots = ((slots_mod + ((slots_mod >> 31) & 3)) >> 2)
        if slots < EquipmentSlots.MIN:
            slots = EquipmentSlots.MIN.value
        elif slots > EquipmentSlots.MAX:
            slots = EquipmentSlots.MAX.value
        equipment['slots_range'].append(slots)
        ab_mod = equipment['max_ability_rolls_modifier'] + i - 4
        ab_rolls = (ab_mod + ((ab_mod >> 31) & 7)) >> 3
        equipment['max_ability_rolls_range'].append(ab_rolls)

    equipment['ability_arrays'] = {}
    for c, i in zip(CHARACTERS.values(), range(178, 371, 32)):
        equipment['ability_arrays'][c.name] = get_abilities(i)

    armored = bool(prize_struct[40] & 0b00000001)
    zanmato_level = prize_struct[402]
    monster = Monster(
        name=monster_name,
        stats=stats,
        elemental_affinities=elemental_affinities,
        status_resistances=status_resistances,
        zanmato_level=zanmato_level,
        armored=armored,
        undead=undead,
        auto_statuses=auto_statuses,
        gil=gil,
        ap=ap,
        item_1=item_1,
        item_2=item_2,
        steal=steal,
        bribe=bribe,
        equipment=equipment,
    )
    return monster


PRIZE_STRUCTS = _get_prize_structs('data/ffx_mon_data.csv')

if '-ps2' not in sys.argv:
    PRIZE_STRUCTS = _patch_prize_structs_for_hd(PRIZE_STRUCTS)
else:
    print('Tracker opened in ps2 mode.')
MONSTERS = {k: _get_monster_data(k, v) for k, v in PRIZE_STRUCTS.items()}
