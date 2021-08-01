import csv
import sys
import os
from typing import Iterator, Union, Optional

Value = Union[str, int]


def get_resource_path(relative_path: str) -> str:
    '''Converts a relative path to an absolute path.
    Necessary for https://github.com/brentvollebregt/auto-py-to-exe .
    '''
    base_path = getattr(
        sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)


class FFXRNGTracker:

    # static variables
    TIDUS = 'Tidus'
    YUNA = 'Yuna'
    AURON = 'Auron'
    KIMAHRI = 'Kimahri'
    WAKKA = 'Wakka'
    LULU = 'Lulu'
    RIKKU = 'Rikku'
    SEYMOUR = 'Seymour'
    VALEFOR = 'Valefor'
    IFRIT = 'Ifrit'
    IXION = 'Ixion'
    SHIVA = 'Shiva'
    BAHAMUT = 'Bahamut'

    CHARACTERS = (
        TIDUS,
        YUNA,
        AURON,
        KIMAHRI,
        WAKKA,
        LULU,
        RIKKU,
        SEYMOUR,
        VALEFOR,
        IFRIT,
        IXION,
        SHIVA,
        BAHAMUT,
    )

    class SeedNotFoundError(Exception):
        '''Raised when no seed is found.'''
        pass

    class InvalidDamageRollError(Exception):
        '''Raised when a damage roll provided as input is not valid.'''
        pass

    def __init__(
            self,
            damage_rolls_input: tuple[int, int, int, int, int, int]) -> None:

        # checks for valid damage rolls
        self.damage_rolls = self.check_damage_rolls(damage_rolls_input)

        # retrieves the 68 initial rng seeds values and the seed number
        self.rng_initial_values, self.seed_number = self.get_rng_seed(
            'files/ffxhd-raw-rng-arrays.csv')

        if self.seed_number == 0:
            raise self.SeedNotFoundError('Seed not found')

        self.rng_arrays = {
            # encouter formations and preempt/ambush chance
            0: self.get_rng_array(0, 5000),
            # drop/steal chance
            10: self.get_rng_array(10, 5000),
            # rare item chance
            11: self.get_rng_array(11, 5000),
            # equipment owner,type, number of slots and abilities
            12: self.get_rng_array(12, 5000),
            # abilities
            13: self.get_rng_array(13, 5000),
        }

        # used to keep track of the rng positions
        self.rng_current_positions = {}

        # get the party's damage/crit/escape arrays
        for i in range(20, 28):
            self.rng_arrays[i] = self.get_rng_array(i, 5000)
            self.rng_current_positions[i] = 0

        # get all the status chance arrays
        for i in range(52, 68):
            self.rng_arrays[i] = self.get_rng_array(i)
            self.rng_current_positions[i] = 0

        self.abilities = self.get_ability_names('files/ffxhd-abilities.csv')
        self.equipment_names = self.get_equipment_names(
            'files/ffxhd-equipment-names.csv')
        self.items = self.get_item_names('files/ffxhd-items.csv')
        self.text_characters = self.get_text_characters(
            'files/ffxhd-characters.csv')
        self.monsters_data = self.get_monsters_data(
            'files/ffxhd-mon_data.csv')
        self.formations = self.get_formations('files/ffxhd-formations.csv')

        # temporary workaround
        # ffxhd-mon_data.csv has PS2 NA version monsters information
        self._patch_monsters_dict_for_hd()

        # sets variables to their starting positions
        self.reset_variables()

    def check_damage_rolls(
            self,
            damage_rolls_input: tuple[int, int, int, int, int, int]) -> dict[str, dict[int, int]]:
        '''Checks if the damage rolls are valid.'''
        damage_rolls = {'tidus': {}, 'auron': {}}

        possible_rolls = {
            'tidus': (
                125, 126, 127, 128, 129, 130, 131, 132, 133,
                134, 135, 136, 137, 138, 139, 140, 141
            ),
            'auron': (
                260, 261, 262, 263, 264, 266, 267, 268, 269, 270, 271,
                272, 273, 274, 275, 276, 278, 279, 280, 281, 282, 283,
                284, 285, 286, 287, 288, 289, 291, 292, 293, 294
            )
        }

        for i in range(3):
            damage_rolls['auron'][i + 1] = damage_rolls_input[(i * 2)]
            damage_rolls['tidus'][i + 1] = damage_rolls_input[(i * 2) + 1]

        for character in ('tidus', 'auron'):
            for index, damage_roll in damage_rolls[character].items():
                if damage_roll not in possible_rolls[character]:
                    if damage_roll // 2 not in possible_rolls[character]:
                        raise self.InvalidDamageRollError(
                            f'Invalid damage roll: {character} {damage_roll}')
                    else:
                        damage_rolls[character][index] = damage_roll // 2

        return damage_rolls

    def get_rng_seed(self, rng_file: str) -> tuple[list[Optional[int]], int]:
        '''Retrieves the initial rng array values.'''
        damage_rolls = self.damage_rolls

        with open(get_resource_path(rng_file)) as abilities_file_object:
            rng_file_reader = csv.reader(abilities_file_object, delimiter=',')
            seed_number = 0
            for seed in rng_file_reader:
                if seed_number == 0:
                    pass
                else:
                    if (damage_rolls['auron'][1] == int(seed[0])
                            and damage_rolls['auron'][2] == int(seed[2])
                            and damage_rolls['auron'][3] == int(seed[4])
                            and damage_rolls['tidus'][1] == int(seed[1])
                            and damage_rolls['tidus'][2] == int(seed[3])
                            and damage_rolls['tidus'][3] == int(seed[5])):
                        # first 6 values of the array are the damage rolls
                        seed = seed[6:]
                        current_seed_values = [int(value) for value in seed]
                        return current_seed_values, seed_number
                seed_number += 1
        # if no seed found
        return [None], 0

    def rng_array_generator(self, rng_index: int) -> Iterator[int]:
        '''Returns a generator object that yields rng values for a given rng
        index. This is the actual ShuffleRNGSeed function used in the game.
        '''
        def s32(integer: int) -> int:
            '''Used as part of the ShuffleRNGSeed function.'''
            integer = integer & 0xffffffff
            return (integer ^ 0x80000000) - 0x80000000

        rng_constants_1 = (
            2100005341, 1700015771, 247163863, 891644838, 1352476256,
            1563244181, 1528068162, 511705468, 1739927914, 398147329,
            1278224951, 20980264, 1178761637, 802909981, 1130639188,
            1599606659, 952700148, -898770777, -1097979074, -2013480859,
            -338768120, -625456464, -2049746478, -550389733, -5384772,
            -128808769, -1756029551, 1379661854, 904938180, -1209494558,
            -1676357703, -1287910319, 1653802906, 393811311, -824919740,
            1837641861, 946029195, 1248183957, -1684075875, -2108396259,
            -681826312, 1003979812, 1607786269, -585334321, 1285195346,
            1997056081, -106688232, 1881479866, 476193932, 307456100,
            1290745818, 162507240, -213809065, -1135977230, -1272305475,
            1484222417, -1559875058, 1407627502, 1206176750, -1537348094,
            638891383, 581678511, 1164589165, -1436620514, 1412081670,
            -1538191350, -284976976, 706005400
        )

        rng_constants_2 = (
            10259, 24563, 11177, 56952, 46197, 49826, 27077, 1257, 44164,
            56565, 31009, 46618, 64397, 46089, 58119, 13090, 19496, 47700,
            21163, 16247, 574, 18658, 60495, 42058, 40532, 13649, 8049,
            25369, 9373, 48949, 23157, 32735, 29605, 44013, 16623, 15090,
            43767, 51346, 28485, 39192, 40085, 32893, 41400, 1267, 15436,
            33645, 37189, 58137, 16264, 59665, 53663, 11528, 37584, 18427,
            59827, 49457, 22922, 24212, 62787, 56241, 55318, 9625, 57622,
            7580, 56469, 49208, 41671, 36458
        )

        rng_value = self.rng_initial_values[rng_index]
        rng_constant_1 = s32(rng_constants_1[rng_index])
        rng_constant_2 = rng_constants_2[rng_index]

        while True:
            rng_value = s32(s32(rng_value) * rng_constant_1 ^ rng_constant_2)
            rng_value = s32((rng_value >> 0x10) + (rng_value << 0x10))
            yield rng_value & 0x7fffffff

    def get_rng_array(
            self, rng_index: int, number_of_values: int = 1000) -> list[int]:
        '''Returns the first n number of values for the given rng index.'''
        rng_generator = self.rng_array_generator(rng_index)
        rng_values = []
        for _ in range(number_of_values):
            rng_values.append(next(rng_generator))
        return rng_values

    def advance_rng(self, rng_index: int) -> int:
        '''Advances the position of the given rng index and returns
        the next value for that index.
        '''
        position = self.rng_current_positions[rng_index]
        rng_value = self.rng_arrays[rng_index][position]
        self.rng_current_positions[rng_index] += 1
        return rng_value

    def reset_variables(self) -> None:
        '''Sets the state of some variables to their starting position.'''
        self.rng_current_positions[0] = 0
        self.rng_current_positions[10] = 0
        self.rng_current_positions[11] = 0
        self.rng_current_positions[12] = 0
        self.rng_current_positions[13] = 0
        # used to store all the events that roll rng
        self.events_sequence = []
        # used to keep track of characters eligible for equipment drops
        self.current_party_formation = {
            self.TIDUS: True,
            self.YUNA: False,
            self.AURON: True,
            self.KIMAHRI: False,
            self.WAKKA: False,
            self.LULU: False,
            self.RIKKU: False
        }

    def get_ability_names(
            self, abilities_file: str) -> list[dict[str, Value]]:
        '''Retrieves the abilities names and their base gil values
        used in the equipment price formula.
        '''
        with open(get_resource_path(abilities_file)) as abilities_file_object:
            abilities_file_reader = csv.reader(
                abilities_file_object, delimiter=',')
            # skips first line
            next(abilities_file_reader)
            ability_names = [{'name': line[1], 'gil_value': int(line[2])}
                             for line in abilities_file_reader]
        return ability_names

    def get_equipment_names(
            self, equipment_names_file: str) -> dict[str, list[str]]:
        '''Retrieves the equipment names.'''
        equipment_names = {'weapon': [], 'armor': []}
        with open(get_resource_path(equipment_names_file)) as \
                equipment_names_file_object:
            equipment_names_file_reader = csv.reader(
                equipment_names_file_object, delimiter=',')
            # skips first 3 lines
            for _ in range(3):
                next(equipment_names_file_reader)
            # get weapons' names lists
            for _ in range(66):
                equipment_names['weapon'].append(
                    next(equipment_names_file_reader))
            # skips empty line
            next(equipment_names_file_reader)
            # get armors' names lists
            for _ in range(84):
                equipment_names['armor'].append(
                    next(equipment_names_file_reader))
        return equipment_names

    def get_item_names(self, items_file: str) -> list[str]:
        '''Retrieves the items names.'''
        with open(get_resource_path(items_file)) as items_file_object:
            items_file_reader = csv.reader(items_file_object, delimiter=',')
            # skips first line
            next(items_file_reader)
            items_list = [line[1] for line in items_file_reader]
        return items_list

    def get_formations(self, formations_file):
        '''Retrieves the encounter formations.'''
        formations_list = {}
        with open(get_resource_path(formations_file)) as formations_file_object:
            formations_file_reader = csv.reader(
                formations_file_object, delimiter=',')
            for line in formations_file_reader:
                for index, cell in enumerate(line):
                    if index == 0:
                        zone = cell
                        formations_list[zone] = []
                    else:
                        formations_list[zone].append(cell)
        return formations_list

    def get_text_characters(self, characters_file: str) -> dict[int, str]:
        '''Retrieves the character encoding chart used in prize structs.'''
        with open(get_resource_path(characters_file)) as \
                characters_file_object:
            text_characters_file_reader = csv.reader(
                characters_file_object, delimiter=',')
            # skips first line
            next(text_characters_file_reader)
            text_characters_dict = {}
            for line in text_characters_file_reader:
                text_characters_dict[int(line[0])] = line[2]
        return text_characters_dict

    def get_monsters_data(
            self, monster_data_file: str) -> dict[str, list[int]]:
        '''Retrieves the prize structs for enemies.'''
        with open(get_resource_path(monster_data_file)) as \
                monster_data_file_object:
            monster_data_file_reader = csv.reader(
                monster_data_file_object, delimiter=',')
            # skips first line
            next(monster_data_file_reader)
            monsters_data = {}

            for line in monster_data_file_reader:
                prize_struct = [int(value, 16) for value in line]
                # gets the name of the monster from the prize struct itself
                # name is null (0x00) terminated
                monster_name = ''
                for i in range(408, 430):
                    if prize_struct[i] == 0:
                        break
                    monster_name += self.text_characters[prize_struct[i]]
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

    def _patch_monsters_dict_for_hd(self) -> None:
        '''Temporary workaround,
        ffxhd-mon_data.csv has PS2 NA version monsters information.
        '''
        def patch_abilities(
                name: str,
                abilities: tuple[int, int, int, int, int, int, int],
                equipment_type: str = 'weapon') -> None:
            '''Modifies ability values 1-7 of every character's weapon
            or armor ability array.
            '''
            # base address for abilities in the prize struct
            base_address = 178
            type_offset = 0 if equipment_type == 'weapon' else 1
            # place the abilities values at the correct offsets
            for owner_index in range(7):
                offset = (type_offset + (owner_index * 2)) * 16
                for slot in range(7):
                    slot_offset = (slot + 1) * 2
                    address = base_address + offset + slot_offset
                    self.monsters_data[name][address] = abilities[slot]

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
            self.monsters_data[monster_name][139] = 12

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

    def get_spoils(
            self, monster_name: str, killer_index: int,
            current_party_formation: dict[str, bool]) -> tuple[Optional[dict[str, Value]], Optional[dict[str, Value]], Optional[dict[str, Value]]]:
        '''Returns drops obtained from killing an enemy
        at the current rng position and advances rng accordingly.
        '''
        prize_struct = self.monsters_data[monster_name]

        item1_drop_chance = prize_struct[136]
        rng_item1_drop = self.advance_rng(10)
        if item1_drop_chance > (rng_item1_drop % 255):
            rng_item1_rarity = self.advance_rng(11)
            item1_common = False if ((rng_item1_rarity & 255) < 32) else True
            item1 = self._get_item1(monster_name, item1_common)
        else:
            item1 = None

        item2_drop_chance = prize_struct[137]
        rng_item2_drop = self.advance_rng(10)
        if item2_drop_chance > (rng_item2_drop % 255):
            rng_item2_rarity = self.advance_rng(11)
            item2_common = False if ((rng_item2_rarity & 255) < 32) else True
            item2 = self._get_item2(monster_name, item2_common)
        else:
            item2 = None

        equipment_drop_chance = prize_struct[139]
        rng_equipment_drop = self.advance_rng(10)
        if equipment_drop_chance > (rng_equipment_drop % 255):
            equipment = self.create_dropped_equipment(
                monster_name, killer_index, current_party_formation)
        else:
            equipment = None

        return item1, item2, equipment

    def _get_item1(
            self, monster_name: str, item_common: bool = True,
            overkill: bool = False) -> dict[str, Value]:
        '''Returns name and quantity of the item in the item1 slot
        of an enemy's prize struct.
        '''
        prize_struct = self.monsters_data[monster_name]

        if overkill:
            overkill_offset = 12
        else:
            overkill_offset = 0

        if item_common:
            item_name_address = 140 + overkill_offset
            item_quantity_address = 148 + overkill_offset
            item_rarity = 'common'
        else:
            item_name_address = 142 + overkill_offset
            item_quantity_address = 149 + overkill_offset
            item_rarity = 'rare'

        item = {
            'name': self.items[prize_struct[item_name_address]],
            'quantity': prize_struct[item_quantity_address],
            'rarity': item_rarity,
        }

        return item

    def _get_item2(
            self, monster_name: str, item_common: bool = True,
            overkill: bool = False) -> dict[str, Value]:
        '''Returns name and quantity of the item in the item2 slot
        of an enemy's prize struct.
        '''
        prize_struct = self.monsters_data[monster_name]

        if overkill:
            overkill_offset = 12
        else:
            overkill_offset = 0

        if item_common:
            item_name_address = 144 + overkill_offset
            item_quantity_address = 150 + overkill_offset
            item_rarity = 'common'
        else:
            item_name_address = 146 + overkill_offset
            item_quantity_address = 151 + overkill_offset
            item_rarity = 'rare'

        item = {
            'name': self.items[prize_struct[item_name_address]],
            'quantity': prize_struct[item_quantity_address],
            'rarity': item_rarity,
        }

        return item

    def _fix_out_of_bounds_value(
            self, value: int,
            lower_bound: int = 1, higher_bound: int = 4) -> int:
        '''Used to fix the number of slots in an equipment,
        there must be between 1 and 4.
        '''
        if value < lower_bound:
            value = lower_bound
        elif value > higher_bound:
            value = higher_bound
        return value

    def _get_weapon_name(
            self, owner_index: int, abilities: list[int], slots: int) -> str:
        '''Returns a weapon's name given the owner,
        the abilities and the number of slots.
        '''
        # get number of certain ability types in the equipment
        elemental_strikes = len(
            [a for a in (30, 34, 38, 42) if a in abilities])
        status_strikes = len(
            [a for a in (46, 50, 54, 58, 62, 66, 70, 74) if a in abilities])
        status_touches = len(
            [a for a in (47, 51, 55, 59, 63, 67, 71, 75) if a in abilities])
        strength_bonuses = len(
            [a for a in (98, 99, 100, 101) if a in abilities])
        magic_bonuses = len(
            [a for a in (102, 103, 104, 105) if a in abilities])

        # check conditions for names in order of priority
        if 122 in abilities:  # Capture
            index = 0
        elif elemental_strikes == 4:  # All four elemental -strikes
            index = 1
        elif 25 in abilities:  # Break Damage Limit
            index = 2
        # Triple Overdrive, Triple AP and Overdrive → AP
        elif 15 in abilities and 19 in abilities and 17 in abilities:
            index = 3
        # Triple Overdrive and Overdrive → AP
        elif 15 in abilities and 17 in abilities:
            index = 4
        # Double Overdrive and Double AP
        elif 14 in abilities and 18 in abilities:
            index = 5
        elif 15 in abilities:  # Triple Overdrive
            index = 6
        elif 14 in abilities:  # Double Overdrive
            index = 7
        elif 19 in abilities:  # Triple AP
            index = 8
        elif 18 in abilities:  # Double AP
            index = 9
        elif 17 in abilities:  # Overdrive → AP
            index = 10
        elif 16 in abilities:  # SOS Overdrive
            index = 11
        elif 13 in abilities:  # One MP Cost
            index = 12
        elif status_strikes == 4:  # Any four status -strike
            index = 13
        elif strength_bonuses == 4:  # All four Strength +X%
            index = 14
        elif magic_bonuses == 4:  # All four Magic +X%
            index = 15
        # Magic Booster and three Magic +X%
        elif 6 in abilities and magic_bonuses == 3:
            index = 16
        elif 12 in abilities:  # Half MP Cost
            index = 17
        elif 26 in abilities:  # Gillionaire
            index = 18
        elif elemental_strikes == 3:  # Any three elemental -strike
            index = 19
        elif status_strikes == 3:  # Any three status -strike
            index = 20
        # Magic Counter and Counter-Attack or Evade & Counter
        elif 5 in abilities and (3 in abilities or 4 in abilities):
            index = 21
        # Counter-Attack or Evade & Counter
        elif 3 in abilities or 4 in abilities:
            index = 22
        elif 5 in abilities:  # Magic Counter
            index = 23
        elif 6 in abilities:  # Magic Booster
            index = 24
        elif 7 in abilities:  # Alchemy
            index = 25
        elif 1 in abilities:  # First Strike
            index = 26
        elif 2 in abilities:  # Initiative
            index = 27
        elif 46 in abilities:  # Deathstrike
            index = 28
        elif 74 in abilities:  # Slowstrike
            index = 29
        elif 54 in abilities:  # Stonestrike
            index = 30
        elif 58 in abilities:  # Poisonstrike
            index = 31
        elif 62 in abilities:  # Sleepstrike
            index = 32
        elif 66 in abilities:  # Silencestrike
            index = 33
        elif 70 in abilities:  # Darkstrike
            index = 34
        elif strength_bonuses == 3:  # Any three Strength +X%
            index = 35
        elif magic_bonuses == 3:  # Any three Magic +X%
            index = 36
        elif elemental_strikes == 2:  # Any two elemental -strike
            index = 37
        elif status_touches == 2:  # Any two status -touch
            index = 38
        elif 47 in abilities:  # Deathtouch
            index = 39
        elif 75 in abilities:  # Slowtouch
            index = 40
        elif 55 in abilities:  # Stonetouch
            index = 41
        elif 59 in abilities:  # Poisontouch
            index = 42
        elif 63 in abilities:  # Sleeptouch
            index = 43
        elif 67 in abilities:  # Silencetouch
            index = 44
        elif 71 in abilities:  # Darktouch
            index = 45
        elif 0 in abilities:  # Sensor
            index = 46
        elif 30 in abilities:  # Firestrike
            index = 47
        elif 34 in abilities:  # Icestrike
            index = 48
        elif 38 in abilities:  # Lightningstrike
            index = 49
        elif 42 in abilities:  # Waterstrike
            index = 50
        elif 124 in abilities:  # Distill Power
            index = 51
        elif 125 in abilities:  # Distill Mana
            index = 52
        elif 126 in abilities:  # Distill Speed
            index = 53
        elif 127 in abilities:  # Distill Ability
            index = 54
        elif slots == 4:  # 4-slot weapon
            index = 55
        # Magic +X% and Strength +X%
        elif strength_bonuses >= 1 and magic_bonuses >= 1:
            index = 56
        elif slots == 2 or slots == 3:  # 2 or 3 slot weapon
            index = 57
        elif 104 in abilities or 105 in abilities:  # Magic +10% or Magic +20%
            index = 58
        # Strength +10% or Strength +20%
        elif 100 in abilities or 101 in abilities:
            index = 59
        elif 103 in abilities:  # Magic +5%
            index = 60
        elif 102 in abilities:  # Magic +3%
            index = 61
        elif 99 in abilities:  # Strength +5%
            index = 62
        elif 98 in abilities:  # Strength +3%
            index = 63
        elif 11 in abilities:  # Piercing
            index = 64
        elif slots == 1:  # One slot
            index = 65
        else:  # No slots
            index = 65

        return self.equipment_names['weapon'][index][owner_index]

    def _get_armor_name(
            self, owner_index: int, abilities: list[int], slots: int) -> str:
        '''Returns an armor's name given the owner,
        the abilities and the number of slots.
        '''
        # get number of certain ability types in the equipment
        elemental_eaters = len(
            [a for a in (33, 37, 41, 45) if a in abilities])
        elemental_proofs = len(
            [a for a in (32, 36, 40, 44) if a in abilities])
        status_proofs = len(
            [a for a in (48, 52, 56, 60, 64, 68, 72, 76, 78, 80, 82)
             if a in abilities])
        defense_bonuses = len(
            [a for a in (106, 107, 108, 109) if a in abilities])
        magic_defense_bonuses = len(
            [a for a in (110, 111, 112, 113) if a in abilities])
        hp_bonuses = len([a for a in (114, 115, 116, 117) if a in abilities])
        mp_bonuses = len([a for a in (118, 119, 120, 121) if a in abilities])
        auto_statuses = len(
            [a for a in (84, 85, 86, 87, 88) if a in abilities])
        elemental_soses = len([a for a in (94, 95, 96, 97) if a in abilities])
        status_soses = len(
            [a for a in (89, 90, 91, 92, 93) if a in abilities])

        # check conditions for names in order of priority
        # Break HP Limit and Break MP Limit
        if 23 in abilities and 24 in abilities:
            index = 0
        elif 128 in abilities:  # Ribbon
            index = 1
        elif 23 in abilities:  # Break HP Limit
            index = 2
        elif 24 in abilities:  # Break MP Limit
            index = 3
        elif elemental_eaters == 4:  # Four elemental -eater abilities
            index = 4
        elif elemental_proofs == 4:  # Four elemental -proof abilities
            index = 5
        # Auto Shell, Auto Protect, Auto Reflect and Auto Regen
        elif (84 in abilities
              and 85 in abilities
              and 88 in abilities
              and 87 in abilities):
            index = 6
        # Auto-Potion, Auto Med and Auto Phoenix
        elif 8 in abilities and 9 in abilities and 10 in abilities:
            index = 7
        elif 8 in abilities and 9 in abilities:  # Auto Potion and Auto Med
            index = 8
        elif status_proofs == 4:  # Any four status -proof abilities
            index = 9
        elif defense_bonuses == 4:  # All four Defense +X%
            index = 10
        elif magic_defense_bonuses == 4:  # All four Magic Defense +X%
            index = 11
        elif hp_bonuses == 4:  # All four HP +X%
            index = 12
        elif mp_bonuses == 4:  # All four MP +X%
            index = 13
        elif 22 in abilities:  # Master Thief
            index = 14
        elif 21 in abilities:  # Pickpocket
            index = 15
        elif 27 in abilities and 28 in abilities:  # HP Stroll and MP Stroll
            index = 16
        elif auto_statuses == 3:  # Any three auto- status abilities
            index = 17
        elif elemental_eaters == 3:  # Any three -eater abilities
            index = 18
        elif 27 in abilities:  # HP Stroll
            index = 19
        elif 28 in abilities:  # MP Stroll
            index = 20
        elif 10 in abilities:  # Auto Phoenix
            index = 21
        elif 9 in abilities:  # Auto Med
            index = 22
        elif elemental_soses == 4:  # Four elemental SOS- abilities
            index = 23
        elif status_soses == 4:  # Any four SOS- status abilities
            index = 24
        elif status_proofs == 3:  # Any three status -proof abilities
            index = 25
        elif 29 in abilities:  # No Encounters
            index = 26
        elif 8 in abilities:  # Auto Potion
            index = 27
        elif elemental_proofs == 3:  # Any three elemental -proof abilities
            index = 28
        elif status_soses == 3:  # Any three SOS- status abilities
            index = 29
        elif auto_statuses == 2:  # Any two auto- status abilities
            index = 30
        elif elemental_soses == 2:  # Any two elemental SOS- abilities
            index = 31
        elif 87 in abilities or 92 in abilities:  # Auto Regen or SOS Regen
            index = 32
        elif 86 in abilities or 91 in abilities:  # Auto Haste or SOS Haste
            index = 33
        # Auto Reflect or SOS Reflect
        elif 88 in abilities or 93 in abilities:
            index = 34
        elif 84 in abilities or 89 in abilities:  # Auto Shell or SOS Shell
            index = 35
        # Auto Protect or SOS Protect
        elif 85 in abilities or 90 in abilities:
            index = 36
        elif defense_bonuses == 3:  # Any three Defense +X%
            index = 37
        elif magic_defense_bonuses == 3:  # Any three Magic Defense +X%
            index = 38
        elif hp_bonuses == 3:  # Any three HP +X%
            index = 39
        elif mp_bonuses == 3:  # Any three MP +X%
            index = 40
        # Any two elemental -proof or -eater of different elements
        elif elemental_eaters + elemental_proofs >= 2:
            index = 41
        elif status_proofs == 2:  # Any two status -proof abilities
            index = 42
        elif 33 in abilities:  # Fire Eater
            index = 43
        elif 37 in abilities:  # Ice Eater
            index = 44
        elif 41 in abilities:  # Lightning Eater
            index = 45
        elif 45 in abilities:  # Water Eater
            index = 46
        elif 82 in abilities:  # Curseproof
            index = 47
        elif 78 in abilities or 79 in abilities:  # Confuse Ward/Proof
            index = 48
        elif 80 in abilities or 81 in abilities:  # Berserk Ward/Proof
            index = 49
        elif 76 in abilities or 77 in abilities:  # Slow Ward/Proof
            index = 50
        elif 48 in abilities or 49 in abilities:  # Death Ward/Proof
            index = 51
        elif 52 in abilities or 53 in abilities:  # Zombie Ward/Proof
            index = 52
        elif 56 in abilities or 57 in abilities:  # Stone Ward/Proof
            index = 53
        elif 60 in abilities or 61 in abilities:  # Poison Ward/Proof
            index = 54
        elif 64 in abilities or 65 in abilities:  # Sleep Ward/Proof
            index = 55
        elif 68 in abilities or 69 in abilities:  # Silence Ward/Proof
            index = 56
        elif 72 in abilities or 73 in abilities:  # Dark Ward/Proof
            index = 57
        elif 31 in abilities or 32 in abilities:  # Fire Ward/Proof
            index = 58
        elif 35 in abilities or 36 in abilities:  # Ice Ward/Proof
            index = 59
        elif 39 in abilities or 40 in abilities:  # Lightning Ward/Proof
            index = 60
        elif 43 in abilities or 44 in abilities:  # Water Ward/Proof
            index = 61
        elif 94 in abilities:  # SOS NulTide
            index = 62
        elif 97 in abilities:  # SOS NulBlaze
            index = 63
        elif 96 in abilities:  # SOS NulShock
            index = 64
        elif 95 in abilities:  # SOS NulFrost
            index = 65
        # Any two HP +X% and any two MP +X%
        elif hp_bonuses == 2 and mp_bonuses == 2:
            index = 66
        elif slots == 4:  # Four slots
            index = 67
        # Defense +X% and Magic Defense +X%
        elif defense_bonuses >= 1 and magic_defense_bonuses >= 1:
            index = 68
        elif defense_bonuses == 2:  # Any two Defense +X%
            index = 69
        elif magic_defense_bonuses == 2:  # Any two Magic Defense +X%
            index = 70
        elif hp_bonuses == 2:  # Any two HP +X%
            index = 71
        elif mp_bonuses == 2:  # Any two MP +X%
            index = 72
        # Defense +10% or Defense +20%
        elif 108 in abilities or 109 in abilities:
            index = 73
        # Magic Defense +10% or Magic Defense +20%
        elif 112 in abilities or 113 in abilities:
            index = 74
        elif 120 in abilities or 121 in abilities:  # MP +20% or MP +30%
            index = 75
        elif 116 in abilities or 117 in abilities:  # HP +20% or HP +30%
            index = 76
        elif slots == 3:  # Three slots
            index = 77
        # Defense +3% or Defense +5%
        elif 106 in abilities or 107 in abilities:
            index = 78
        # Magic Defense +3% or Magic Defense +5%
        elif 110 in abilities or 111 in abilities:
            index = 79
        elif 118 in abilities or 119 in abilities:  # MP +5% or MP +10%
            index = 80
        elif 114 in abilities or 115 in abilities:  # HP +5% or HP +10%
            index = 81
        elif slots == 2:  # Two slots
            index = 82
        elif slots == 1:  # One slot
            index = 83
        else:  # No slots
            index = 83

        return self.equipment_names['armor'][index][owner_index]

    def create_dropped_equipment(
            self, monster_name: str,
            killer_index: int,
            current_party_formation: dict[str, bool]) -> dict[str, Value]:
        '''Returns equipment obtained from killing an enemy
        at the current rng position and advances rng accordingly.
        '''
        characters_enabled = list(current_party_formation.values())

        prize_struct = self.monsters_data[monster_name]

        equipment = {
            'monster_name': monster_name,
            'killer_index': killer_index,
        }

        equipment_owner_base = 0

        # get number of party members enabled
        for party_member_index in range(7):
            if characters_enabled[party_member_index]:
                equipment_owner_base += 1

        rng_equipment_owner = self.advance_rng(12)

        # check if killing with a party member
        # always gives the equipment to that character
        killer_is_owner_test = rng_equipment_owner % (equipment_owner_base + 3)
        if killer_is_owner_test > equipment_owner_base:
            equipment['killer_is_owner'] = True
        else:
            equipment['killer_is_owner'] = False

        # if the killer is a party member (0-6)
        # it gives them a bonus chance for the equipment to be theirs
        if killer_index < 7:
            owner_index = killer_index
            equipment_owner_base += 3
        else:
            owner_index = 0

        rng_equipment_owner = rng_equipment_owner % equipment_owner_base
        number_of_enabled_party_members = 0

        # get equipment owner
        for party_member_index in range(7):
            if characters_enabled[party_member_index]:
                number_of_enabled_party_members += 1
                if rng_equipment_owner < number_of_enabled_party_members:
                    owner_index = party_member_index
                    break

        equipment['owner'] = self.CHARACTERS[owner_index]

        # get equipment type
        rng_weapon_or_armor = self.advance_rng(12) & 1
        equipment_type = rng_weapon_or_armor
        equipment['type'] = 'weapon' if (equipment_type) == 0 else 'armor'

        # 255 not equipped, 0 equipped
        equipment['0_if_equipped'] = 255
        # 0 for enemies that can never drop equipment
        equipment['exists'] = prize_struct[174]
        # base weapon damage, 16 or 18
        equipment['base_weapon_damage'] = prize_struct[176]
        # bonus weapon crit, 3, 6 or 10
        equipment['bonus_weapon_crit'] = prize_struct[175]

        # get number of slots
        rng_number_of_slots = self.advance_rng(12) & 7
        slots_mod = (prize_struct[173]
                     + rng_number_of_slots
                     - 4)
        number_of_slots = (slots_mod + ((slots_mod >> 31) & 3)) >> 2
        number_of_slots = self._fix_out_of_bounds_value(number_of_slots)
        equipment['slots'] = number_of_slots

        # get number of abilities
        rng_number_of_abilities = self.advance_rng(12) & 7
        abilities_mod = (prize_struct[177]
                         + rng_number_of_abilities
                         - 4)
        ability_rolls = (abilities_mod + ((abilities_mod >> 31) & 7)) >> 3

        # get offset of the abilities array based on weapon/armor
        # and equipment owner
        owner_offset = owner_index * 2 * 16
        type_offset = equipment_type * 16
        abilities_array_offset = 178 + owner_offset + type_offset

        # this byte is usually null (0x00) but for kimahri and auron's weapons
        # and for drops from specific enemies corresponds to an ability
        forced_ability = prize_struct[abilities_array_offset]
        # the forced ability gets applied only if this byte is 0x80
        forced_ability_check = prize_struct[abilities_array_offset + 1]

        equipment['abilities'] = []
        equipment['abilities_index'] = []
        equipment['base_gil_value'] = 0

        # if there is an ability in the first slot of the abilities array
        # it always gets added as long as the equipment has slots
        if number_of_slots == 0 or forced_ability_check == 0:
            number_of_abilities_added = 0
        else:
            equipment['abilities_index'].append(forced_ability)
            equipment['abilities'].append(
                self.abilities[forced_ability]['name'])
            equipment['base_gil_value'] += self.abilities[forced_ability]['gil_value']
            number_of_abilities_added = 1

        if ability_rolls > 0:

            for _ in range(ability_rolls):

                # if all the slots are filled break
                if number_of_abilities_added >= number_of_slots:
                    break

                # get a random ability, picks from ability 1 to ability 7
                rng_abilities_array_index = self.advance_rng(13) % 7 + 1
                ability_to_add_offset = (abilities_array_offset
                                         + rng_abilities_array_index * 2)
                ability_to_add = prize_struct[ability_to_add_offset]
                ability_to_add_check = prize_struct[ability_to_add_offset + 1]

                # if the ability is not null
                if ability_to_add_check != 0:

                    add_ability = True

                    # check for duplicate abilities
                    for slot in range(number_of_abilities_added):

                        ability_to_check = equipment['abilities_index'][slot]

                        # if the ability has already been added stop checking
                        if ability_to_check == ability_to_add:
                            add_ability = False
                            break

                    # if the ability is not a duplicate add it to the current
                    # slot and advance both slot count and ability added count
                    if add_ability:
                        equipment['abilities_index'].append(ability_to_add)
                        equipment['abilities'].append(
                            self.abilities[ability_to_add]['name'])
                        equipment['base_gil_value'] += self.abilities[ability_to_add]['gil_value']
                        number_of_abilities_added += 1

        # set empty slots
        for _ in range(number_of_slots - number_of_abilities_added):
            equipment['abilities'].append('-')

        # if enemy equipment droprate is 100%
        if prize_struct[139] == 255:
            equipment['guaranteed'] = True
        else:
            equipment['guaranteed'] = False

        # calculate buy and sell gil values
        slots_factor = (1, 1, 1.5, 3, 5)
        empty_slots_factor = (1, 1, 1.5, 3, 400)
        equipment['buy_gil_value'] = int(
            (50 + equipment['base_gil_value'])
            * slots_factor[number_of_slots]
            * empty_slots_factor[number_of_slots - number_of_abilities_added])
        equipment['sell_gil_value'] = equipment['buy_gil_value'] // 4

        # get equipment name
        if equipment['type'] == 'weapon':
            equipment['name'] = self._get_weapon_name(
                owner_index, equipment['abilities_index'], number_of_slots)
        elif equipment['type'] == 'armor':
            equipment['name'] = self._get_armor_name(
                owner_index, equipment['abilities_index'], number_of_slots)

        return equipment

    def get_stolen_item(
            self, monster_name: str,
            successful_steals: int = 0) -> Optional[dict[str, Value]]:
        '''Returns the item obtained from stealing from an enemy
        at the current rng position and advances rng accordingly.
        '''
        prize_struct = self.monsters_data[monster_name]

        if prize_struct is None:
            return None

        steal_chance = prize_struct[138] // (2 ** successful_steals)
        rng_steal = self.advance_rng(10)
        if steal_chance > (rng_steal % 255):
            rng_steal_rarity = self.advance_rng(11)
            item_common = False if ((rng_steal_rarity & 255) < 32) else True
            if item_common:
                item_name_address = 164
                item_quantity_address = 168
                item_rarity = 'common'
            else:
                item_name_address = 166
                item_quantity_address = 169
                item_rarity = 'rare'

            item = {
                'name': self.items[prize_struct[item_name_address]],
                'quantity': prize_struct[item_quantity_address],
                'rarity': item_rarity,
            }

        else:
            item = None

        return item

    def get_equipment_types(self, amount: int = 50) -> list[str]:
        '''Returns a list of equipments types in the current seed,
        one of the properties of equipment that can't be changed.
        '''
        equipment_types = []
        for i in range(amount):
            # the equipment type is only determined by the seed
            # the rng position used to determine it is the second one
            # out of the 4 used for every equipment
            rng_weapon_or_armor = self.rng_arrays[12][(i * 4) + 1]
            equipment_type = rng_weapon_or_armor & 1
            equipment_type = 'weapon' if (equipment_type) == 0 else 'armor'
            equipment_types.append(equipment_type)
        return equipment_types

    def get_status_chance_rolls(
            self, amount: int = 30) -> dict[int, list[int]]:
        '''Get the first n rolls of the status rng arrays
        for both party members and enemies
        '''
        status_rolls = {}
        for i in range(52, 68):
            status_rolls[i] = []
            for j in range(amount):
                status_rolls[i].append(self.rng_arrays[i][j] % 101)
        return status_rolls

    def add_steal_event(
            self, monster_name: str, successful_steals: int = 0) -> None:
        '''Creates a steal event and appends it to the events list.'''
        event = {
            'name': 'steal',
            'monster_name': monster_name,
        }
        event['item'] = self.get_stolen_item(monster_name, successful_steals)
        self.events_sequence.append(event)

    def add_kill_event(self, monster_name: str, killer: str) -> None:
        '''Creates a enemy kill event and appends it to the events list.'''
        monster_name = monster_name.lower().replace(' ', '_')
        event = {
            'name': 'kill',
            'monster_name': monster_name,
            'killer': killer,
        }
        killer = f'{killer[0].upper()}{killer[1:].lower()}'

        try:
            killer_index = self.CHARACTERS.index(killer)
        except ValueError:
            killer_index = 7

        event['item1'], event['item2'], event['equipment'] = self.get_spoils(
            monster_name, killer_index, self.current_party_formation)
        self.events_sequence.append(event)

    def add_death_event(self, dead_character: str = 'Unknown') -> None:
        '''Creates a character death event
        and appends it to the events list.
        '''
        event = {
            'name': 'death',
            'dead_character': dead_character,
        }
        self.rng_current_positions[10] += 3
        self.events_sequence.append(event)

    def add_advance_rng_event(
            self, rng_index: int, number_of_times: int = 1) -> None:
        '''Creates an advance rng event and appends it to the events list,
        advances the position of a particular rng index.
        '''
        event = {
            'name': 'advance_rng',
            'rng_index': rng_index,
            'number_of_times': number_of_times,
        }
        self.rng_current_positions[rng_index] += number_of_times
        self.events_sequence.append(event)

    def add_change_party_event(self, party_formation: str) -> None:
        '''Creates a changed party formation event and appends it
        to the events list, modifies the current party formation dict.
        '''
        self.current_party_formation = {
            self.TIDUS: False,
            self.YUNA: False,
            self.AURON: False,
            self.KIMAHRI: False,
            self.WAKKA: False,
            self.LULU: False,
            self.RIKKU: False
        }

        new_party_formation = []

        if 't' in party_formation:
            self.current_party_formation[self.TIDUS] = True
            new_party_formation.append(self.TIDUS)
        if 'y' in party_formation:
            self.current_party_formation[self.YUNA] = True
            new_party_formation.append(self.YUNA)
        if 'a' in party_formation:
            self.current_party_formation[self.AURON] = True
            new_party_formation.append(self.AURON)
        if 'k' in party_formation:
            self.current_party_formation[self.KIMAHRI] = True
            new_party_formation.append(self.KIMAHRI)
        if 'w' in party_formation:
            self.current_party_formation[self.WAKKA] = True
            new_party_formation.append(self.WAKKA)
        if 'l' in party_formation:
            self.current_party_formation[self.LULU] = True
            new_party_formation.append(self.LULU)
        if 'r' in party_formation:
            self.current_party_formation[self.RIKKU] = True
            new_party_formation.append(self.RIKKU)
        event = {
            'name': 'change_party',
            'party': new_party_formation,
        }
        self.events_sequence.append(event)

    def add_comment_event(self, text: str) -> None:
        '''Creates a comment event, appends a comment to the event list.'''
        event = {
            'name': 'comment',
            'text': text,
        }
        self.events_sequence.append(event)
