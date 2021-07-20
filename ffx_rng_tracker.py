import csv
import sys
import os
from typing import Iterator, Union, Optional

Value = Union[str, int]


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

	CHARACTERS = (TIDUS, YUNA, AURON, KIMAHRI, WAKKA, LULU, RIKKU, SEYMOUR, VALEFOR, IFRIT, IXION, SHIVA, BAHAMUT)

	# raised when no seed found is found
	class SeedNotFoundError(Exception):
		pass


	def __init__(self, damage_rolls_input: tuple[int, int, int, int, int, int]) -> None:

		# checks for valid damage rolls
		self.damage_rolls = self.check_damage_rolls(damage_rolls_input)

		# retrieves the 68 initial rng seeds values and the seed number
		self.rng_initial_values, self.seed_number = self.get_rng_seed('files/ffxhd-raw-rng-arrays.csv')

		if self.seed_number == 0:
			raise SeedNotFoundError('Seed not found')

		self.rng_arrays = {	10: self.get_rng_array(10, 1000),
							11: self.get_rng_array(11, 200),
							12: self.get_rng_array(12, 200),
							13: self.get_rng_array(13, 100),
							}

		self.abilities = self.get_ability_names('files/ffxhd-abilities.csv')
		self.items = self.get_item_names('files/ffxhd-items.csv')
		self.text_characters = self.get_text_characters('files/ffxhd-characters.csv')
		self.monsters_data = self.get_monsters_data('files/ffxhd-mon_data.csv')

		# temporary workaround, ffxhd-mon_data.csv has PS2 NA version monsters information
		self._patch_monsters_dict_for_hd()

		# sets variables to their starting positions
		self.reset_variables()


	def check_damage_rolls(self, damage_rolls_input: tuple[int, int, int, int, int, int]) -> dict[str, dict[int, int]]:

		damage_rolls = {'tidus': {}, 'auron': {}}

		possible_rolls = {	'tidus':(125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141),
							'auron':(260, 261, 262, 263, 264, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 278,
										279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 291, 292, 293, 294)
							}

		(damage_rolls['auron'][1], damage_rolls['tidus'][1], damage_rolls['auron'][2], damage_rolls['tidus'][2], 
			damage_rolls['auron'][3], damage_rolls['tidus'][3]) = damage_rolls_input

		for character in ('tidus', 'auron'):
			for index, damage_roll in damage_rolls[character].items():
				if damage_roll not in possible_rolls[character]:
					if damage_roll // 2 not in possible_rolls[character]:
						raise Exception(f'Invalid damage roll: {damage_roll}')
					else:
						damage_rolls[character][index] = damage_roll // 2

		return damage_rolls


	# necessary for https://github.com/brentvollebregt/auto-py-to-exe
	def get_resource_path(self, relative_path: str) -> str:
		base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
		return os.path.join(base_path, relative_path)


	# returns a tuple with the initial rng values and the seed number
	def get_rng_seed(self, rng_file: str) -> tuple[list[Optional[int]], int]:

		damage_rolls = self.damage_rolls

		with open(self.get_resource_path(rng_file)) as abilities_file_object:
			rng_file_reader = csv.reader(abilities_file_object, delimiter=',')

			seed_number = 0
			for seed in rng_file_reader:
				if seed_number == 0:
					pass
				else:
					if all([damage_rolls['auron'][1] == int(seed[0]), damage_rolls['auron'][2] == int(seed[2]), damage_rolls['auron'][3] == int(seed[4]),
							damage_rolls['tidus'][1] == int(seed[1]), damage_rolls['tidus'][2] == int(seed[3]), damage_rolls['tidus'][3] == int(seed[5])]):

						# first 6 values of the array are the seed damage rolls
						current_seed_values = [int(value) for value in seed[6:]]

						return current_seed_values, seed_number

				seed_number += 1

		# if no seed found
		return [None], 0


	# return a generator object that yields rng values
	def rng_array_generator(self, rng_index: int) -> Iterator[int]:

		def s32(integer):
			integer = integer & 0xffffffff
			return (integer ^ 0x80000000) - 0x80000000

		rng_constants_1 = (2100005341, 1700015771, 247163863, 891644838, 1352476256, 1563244181, 1528068162, 511705468, 1739927914, 398147329, 1278224951, 
			20980264, 1178761637, 802909981, 1130639188, 1599606659, 952700148, -898770777, -1097979074, -2013480859, -338768120, -625456464, -2049746478, 
			-550389733, -5384772, -128808769, -1756029551, 1379661854, 904938180, -1209494558, -1676357703, -1287910319, 1653802906, 393811311, 
			-824919740, 1837641861, 946029195, 1248183957, -1684075875, -2108396259, -681826312, 1003979812, 1607786269, -585334321, 1285195346, 
			1997056081, -106688232, 1881479866, 476193932, 307456100, 1290745818, 162507240, -213809065, -1135977230, -1272305475, 1484222417, -1559875058, 
			1407627502, 1206176750, -1537348094, 638891383, 581678511, 1164589165, -1436620514, 1412081670, -1538191350, -284976976, 706005400)

		rng_constants_2 = (10259, 24563, 11177, 56952, 46197, 49826, 27077, 1257, 44164, 56565, 31009, 46618, 64397, 46089, 58119, 13090, 19496, 47700, 
			21163, 16247, 574, 18658, 60495, 42058, 40532, 13649, 8049, 25369, 9373, 48949, 23157, 32735, 29605, 44013, 16623, 15090, 43767, 51346, 
			28485, 39192, 40085, 32893, 41400, 1267, 15436, 33645, 37189, 58137, 16264, 59665, 53663, 11528, 37584, 18427, 59827, 49457, 22922, 
			24212, 62787, 56241, 55318, 9625, 57622, 7580, 56469, 49208, 41671, 36458)

		rng_value = self.rng_initial_values[rng_index]

		rng_constant_1 = s32(rng_constants_1[rng_index])

		rng_constant_2 = rng_constants_2[rng_index]

		while True:
			rng_value = s32(s32(rng_value) * rng_constant_1 ^ rng_constant_2)
			rng_value = s32((rng_value >> 0x10) + (rng_value << 0x10))
			yield rng_value & 0x7fffffff


	def get_rng_array(self, rng_index: int, number_of_values: int = 1000) -> list[int]:

		rng_generator = self.rng_array_generator(rng_index)

		rng_values = []

		for i in range(number_of_values):
			rng_values.append(next(rng_generator))

		return rng_values


	# advances the position of the rng_index rng array and returns the next rng value
	def advance_rng(self, rng_index: int) -> int:

		rng_value = self.rng_arrays[rng_index][self.rng_current_positions[rng_index]]

		self.rng_current_positions[rng_index] += 1

		return rng_value


	# sets variables back to their starting positions
	def reset_variables(self) -> None:

		# used to keep track of the rng positions
		self.rng_current_positions = {10: 0, 11: 0, 12: 0, 13: 0}

		# used to store all the events that roll rng
		self.events_sequence = []

		# used to keep track of characters eligible for equipment drops
		self.current_party_formation = {self.TIDUS: True, 
										self.YUNA: False, 
										self.AURON: True, 
										self.KIMAHRI: False, 
										self.WAKKA: False, 
										self.LULU: False, 
										self.RIKKU: False}


	# retrieves the ability names and their base gil value used in the equipment price formula
	def get_ability_names(self, abilities_file: str) -> list[dict[str, Value]]:

		with open(self.get_resource_path(abilities_file)) as abilities_file_object:
			abilities_file_reader = csv.reader(abilities_file_object, delimiter=',')

			# skips first line
			next(abilities_file_reader)

			ability_names = [{'name': line[1], 'gil_value': int(line[2])} for line in abilities_file_reader]

		return ability_names


	# retrieves the items names
	def get_item_names(self, items_file: str) -> list[str]:

		with open(self.get_resource_path(items_file)) as items_file_object:
			items_file_reader = csv.reader(items_file_object, delimiter=',')

			# skips first line
			next(items_file_reader)

			items_list = [line[1] for line in items_file_reader]

		return items_list


	# retrieves the text characters table
	def get_text_characters(self, characters_file: str) -> dict[int, str]:

		with open(self.get_resource_path(characters_file)) as characters_file_object:
			text_characters_file_reader = csv.reader(characters_file_object, delimiter=',')

			# skips first line
			next(text_characters_file_reader)

			text_characters_dict = {int(line[0]):line[2] for line in text_characters_file_reader}

		return text_characters_dict


	# retrieves the prize struct of each enemy
	def get_monsters_data(self, monster_data_file: str) -> dict[str, list[int]]:

		with open(self.get_resource_path(monster_data_file)) as monster_data_file_object:
			monster_data_file_reader = csv.reader(monster_data_file_object, delimiter=',')

			# skips first line
			next(monster_data_file_reader)

			monsters_data = {}

			for line in monster_data_file_reader:

				prize_struct = [int(value, 16) for value in line]

				monster_name = ''

				# gets the name of the monster from the prize struct, name always ends in a 0
				for i in range(20):
					if prize_struct[408 + i] == 0: break
					monster_name += self.text_characters[prize_struct[408 + i]]

				monster_name = monster_name.lower().replace(' ', '_')

				if monster_name in monsters_data:
					for i in range(2, 9):
						if f'{monster_name}_{i}' not in monsters_data:
							monsters_data[f'{monster_name}_{i}'] = prize_struct
							break
				else: monsters_data[monster_name] = prize_struct

		return monsters_data


	# temporary workaround, ffxhd-mon_data.csv has PS2 NA version monsters information
	def _patch_monsters_dict_for_hd(self) -> None:

		# modifies ability values 1-8 of every weapon/armor ability array
		# the ability type is almost always a weapon since in the hd version "distill" abilities were introduced
		def patch_abilities(monster_name, abilities_tuple, equipment_type='weapon'):

			# base address for abilities in the prize struct
			base_address = 178

			equipment_type_offset = 0 if equipment_type == 'weapon' else 1

			# place the abilities values at the correct offsets
			for character_index in range(7):
				character_offset = (equipment_type_offset + (character_index * 2)) * 16
				for ability_slot in range(7):
					ability_slot_offset = (ability_slot + 1) * 2
					self.monsters_data[monster_name][base_address + character_offset + ability_slot_offset] = abilities_tuple[ability_slot]


		# in the HD version equipment droprates were modified from 8/255 to 12/255 for these enemies
		for monster_name in ['condor', 'dingo', 'water_flan', 'condor_2', 'dingo_2', 'water_flan_2',
							'dinonix', 'killer_bee', 'yellow_element',
							'worker', 'vouivre', 'raldo',
							'floating_eye', 'ipiria', "mi'ihen_fang", 'raldo_2', 'white_element',
							'funguar', 'gandarewa', 'lamashtu', 'raptor', 'red_element', 'thunder_flan',
							'bite_bug', 'bunyip', 'garm', 'simurgh', 'snow_flan',
							'bunyip_2',
							'aerouge', 'buer', 'gold_element', 'kusariqqu', 'melusine',
							'blue_element', 'iguion', 'murussu', 'wasp',
							'evil_eye', 'ice_flan', 'mafdet', 'snow_wolf', 'guado_guardian_2',
							'alcyone', 'mech_guard', 'mushussu', 'sand_wolf', 'bomb_2', 'evil_eye_2', 'guado_guardian_3',
							'warrior_monk', 'warrior_monk_2',
							'aqua_flan', 'bat_eye', 'cave_iguion', 'sahagin_2', 'swamp_mafdet', 'sahagin_3',
							'flame_flan', 'mech_scouter_2', 'nebiros', 'shred', 'skoll',
							'flame_flan', 'nebiros', 'shred', 'skoll',
							'dark_element', 'imp', 'nidhogg', 'yowie']:
			self.monsters_data[monster_name][139] = 12

		# all the enemies that have ability arrays modified in the HD version
		# abilities
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


	# returns drops obtained from killing an enemy at the current rng position
	# and advances rng accordingly, returning None if there is no drop in that slot
	def get_spoils(self, monster_name: str, killer_index: int, 
		current_party_formation: dict[str, bool]) -> tuple[Optional[dict[str, Value]], Optional[dict[str, Value]], Optional[dict[str, Value]]]:

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
			equipment = self.create_dropped_equipment(monster_name, killer_index, current_party_formation)
		else:
			equipment = None

		return item1, item2, equipment


	# returns name and quantity of the item in the item1 slot
	def _get_item1(self, monster_name: str, item_common: bool = True, overkill: bool = False) -> dict[str, Value]:

		prize_struct = self.monsters_data[monster_name]

		if overkill:
			overkill_offset = 12
		else:
			overkill_offset = 0

		if item_common:
			item_name_address = 140 + overkill_offset
			item_quantity_address = 148 + overkill_offset
		else:
			item_name_address = 142 + overkill_offset
			item_quantity_address = 149 + overkill_offset

		item = {'name': self.items[prize_struct[item_name_address]], 'quantity': prize_struct[item_quantity_address]}

		return item

	# returns name and quantity of the item in the item2 slot
	def _get_item2(self, monster_name: str, item_common: bool = True, overkill: bool = False) -> dict[str, Value]:

		prize_struct = self.monsters_data[monster_name]

		if overkill:
			overkill_offset = 12
		else:
			overkill_offset = 0

		if item_common:
			item_name_address = 144 + overkill_offset
			item_quantity_address = 150 + overkill_offset
		else:
			item_name_address = 146 + overkill_offset
			item_quantity_address = 151 + overkill_offset

		item = {'name': self.items[prize_struct[item_name_address]], 'quantity': prize_struct[item_quantity_address]}

		return item


	# used to calculate the number of slots in an equipment, must be between 1 and 4
	def _fix_out_of_bounds_value(self, value: int, lower_bound: int = 1, higher_bound: int = 4) -> int:

			if value < lower_bound:
				value = lower_bound

			elif value > higher_bound:
				value = higher_bound

			return value


	# returns equipment obtained from killing an enemy at the current rng position and advances rng accordingly
	def create_dropped_equipment(self, monster_name: str, killer_index: int, current_party_formation: dict[str, bool]) -> dict[str, Value]:

		characters_enabled = list(current_party_formation.values())

		prize_struct = self.monsters_data[monster_name]

		equipment = {}

		equipment['monster_name'] = monster_name

		equipment['killer_index'] = killer_index

		# owner
		equipment_owner_base = 0

		# get number of party members enabled
		for party_member_index in range(7):
			if characters_enabled[party_member_index]:
				equipment_owner_base += 1

		if killer_index < 7:
			owner_index = killer_index
			equipment_owner_base += 3
		else:
			owner_index = 0

		rng_equipment_owner = self.advance_rng(12)
		number_of_enabled_party_members = 0
		party_member_index_loop = 0

		# get equipment owner
		for party_member_index in range(7):
			if characters_enabled[party_member_index]:
				number_of_enabled_party_members += 1
				if (rng_equipment_owner % equipment_owner_base) < number_of_enabled_party_members:
					owner_index = party_member_index
					break

		equipment['owner'] = self.CHARACTERS[owner_index]

		# type
		rng_weapon_or_armor = self.advance_rng(12)
		equipment_type = rng_weapon_or_armor & 1
		equipment['type'] = 'weapon' if (equipment_type) == 0 else 'armor'

		# some misc values
		equipment['0_if_equipped'] = 255 # 255 not equipped, 0 equipped
		equipment['exists'] = prize_struct[174]
		equipment['base_weapon_damage'] = prize_struct[176] # base weapon damage, 16 or 18
		equipment['base_weapon_crit'] = prize_struct[175] # base weapon crit, 3-6-10

		# number of slots
		rng_number_of_slots = self.advance_rng(12)
		number_of_slots_modifier = prize_struct[173] + (rng_number_of_slots & 7) - 4
		number_of_slots = self._fix_out_of_bounds_value(((number_of_slots_modifier + ((number_of_slots_modifier >> 31) & 3)) >> 2))
		equipment['slots'] = number_of_slots

		# number of abilities
		rng_number_of_abilities = self.advance_rng(12)
		number_of_abilities_modifier = prize_struct[177] + (rng_number_of_abilities & 7) - 4
		number_of_abilities_max = (number_of_abilities_modifier + ((number_of_abilities_modifier >> 31) & 7)) >> 3

		# get offset of the abilities array based on weapon/armor and equipment owner
		abilities_array_offset = 178 + ((equipment_type + (owner_index * 2)) * 16)

		# the first ability in the array is usually 0x0000 (no ability) for armors, 0x800b (piercing) for weapons
		# some enemies have a different forced ability, for example ??? (kimahri in the boss fight) has sensor in all the weapons
		# and arena fiends have other abilities
		forced_auto_ability_value = prize_struct[abilities_array_offset] + (prize_struct[abilities_array_offset + 1] * 256)

		equipment['abilities'] = []
		equipment['abilities_index'] = []
		equipment['base_gil_value'] = 0

		# if there is an ability in the first slot of the abilities array it always gets added as long as the equipment has slots
		if number_of_slots == 0 or forced_auto_ability_value == 0:
			number_of_abilities_added = 0
		else:
			forced_auto_ability_index = forced_auto_ability_value - 0x8000
			equipment['abilities_index'].append(forced_auto_ability_index)
			equipment['abilities'].append(self.abilities[forced_auto_ability_index]['name'])
			equipment['base_gil_value'] += self.abilities[forced_auto_ability_index]['gil_value']
			number_of_abilities_added = 1

		if number_of_abilities_max > 0:

			for i in range(number_of_abilities_max):

				# if all the slots are filled break
				if number_of_abilities_added >= number_of_slots: break

				# get a random ability, picks from ability 1 to ability 7, ability 0 is always added without rng12 rolls if present
				rng_abilities_array_index = self.advance_rng(13)
				ability_to_add_value = prize_struct[abilities_array_offset + (((rng_abilities_array_index % 7) + 1) * 2)] + (prize_struct[abilities_array_offset + (((rng_abilities_array_index % 7) + 1) * 2) + 1] * 256)

				# if the ability is not null
				if ability_to_add_value != 0:

					ability_to_add_index = ability_to_add_value - 0x8000

					add_ability = True

					# check for duplicate abilities already added to the equipment
					for slot_to_check in range(number_of_abilities_added):

						ability_to_check_index = equipment['abilities_index'][slot_to_check]

						# if the ability has already been added stop checking
						if ability_to_check_index == ability_to_add_index:
							add_ability = False
							break

					# if the ability is not a duplicate add it to the current slot and advance both slot count and ability added count
					if add_ability:
						equipment['abilities_index'].append(ability_to_add_index)
						equipment['abilities'].append(self.abilities[ability_to_add_index]['name'])
						equipment['base_gil_value'] += self.abilities[ability_to_add_index]['gil_value']
						number_of_abilities_added += 1

		# set empty slots
		for i in range(number_of_slots - number_of_abilities_added):
			equipment['abilities'].append('-')

		# add other info
		# if enemy equipment droprate is 100%
		equipment['guaranteed'] = True if (prize_struct[139] == 255) else False

		# calculate buy and sell gil values
		slots_factor = (1, 1, 1.5, 3, 5)
		empty_slots_factor = (1, 1, 1.5, 3, 400)
		equipment['buy_gil_value'] = int((50 + equipment['base_gil_value']) * slots_factor[number_of_slots] * empty_slots_factor[number_of_slots - number_of_abilities_added])
		equipment['sell_gil_value'] = equipment['buy_gil_value'] // 4

		return equipment


	# returns the item obtained from stealing from an enemy at the current rng position
	# and advances rng accordingly
	def get_stolen_item(self, monster_name: str, successful_steals: int = 0) -> Optional[dict[str, Value]]:

		prize_struct = self.monsters_data[monster_name]

		if prize_struct == None:
			return None

		steal_chance = prize_struct[138] // (2 ** successful_steals)

		rng_steal = self.advance_rng(10)

		if steal_chance > (rng_steal % 255):

			rng_steal_rarity = self.advance_rng(11)

			item_common = False if ((rng_steal_rarity & 255) < 32) else True

			if item_common:
				item_name, item_quantity = self.items[prize_struct[164]], prize_struct[168]
			else:
				item_name, item_quantity = self.items[prize_struct[166]], prize_struct[169]

			item = {'name': item_name, 'quantity': item_quantity}

		else:
			item = None

		return item


	# returns a list of equipments types in the current seed
	# since rng12 can't be offset, the equipment types always stay the same
	def get_equipment_types(self, amount: int = 50) -> list[str]:

		equipment_types = []

		for i in range(amount):

			# the equipment type is only determined by the seed and the rng position used to determine it
			# is the second one out of the 4 used for every equipment
			rng_weapon_or_armor = self.rng_arrays[12][(i * 4) + 1]
			equipment_type = rng_weapon_or_armor & 1
			equipment_type = 'weapon' if (equipment_type) == 0 else 'armor'

			equipment_types.append(equipment_type)

		return equipment_types


	# create a steal event and add it to the events list
	def add_steal_event(self, monster_name: str, successful_steals: int = 0) -> None:

		event = {'name': 'steal', 'monster_name': monster_name}

		event['item'] = self.get_stolen_item(monster_name, successful_steals)

		self.events_sequence.append(event)


	# create a enemy kill event and add it to the events list
	def add_kill_event(self, monster_name: str, killer: str) -> None:

		monster_name = monster_name.lower().replace(' ', '_')

		event = {'name': 'kill', 'monster_name': monster_name, 'killer': killer}

		killer = f'{killer[0].upper()}{killer[1:].lower()}'

		try:
			killer_index = self.CHARACTERS.index(killer)
		except ValueError:
			killer_index = 7

		event['item1'], event['item2'], event['equipment'],= self.get_spoils(monster_name, killer_index, self.current_party_formation)

		self.events_sequence.append(event)


	# create a character death event and add it to the events list
	def add_death_event(self, dead_character: str = 'Unknown') -> None:

		event = {'name': 'death', 'dead_character': dead_character}

		self.rng_current_positions[10] += 3

		self.events_sequence.append(event)


	# create an advanced rng event and add it to the events list
	# increments the rng position for a particular rng array
	def add_advance_rng_event(self, rng_index: int, number_of_times: int = 1) -> None:

		event = {'name': 'advance_rng', 'rng_index': rng_index, 'number_of_times': number_of_times}

		self.rng_current_positions[rng_index] += number_of_times

		self.events_sequence.append(event)


	# create a changed party formation event and add it to the events list
	# modifies the current party formation dict
	def add_change_party_event(self, party_formation: str) -> None:

		self.current_party_formation = {self.TIDUS: False, 
										self.YUNA: False, 
										self.AURON: False, 
										self.KIMAHRI: False, 
										self.WAKKA: False, 
										self.LULU: False, 
										self.RIKKU: False}

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

		event = {'name': 'change_party', 'party': new_party_formation}

		self.events_sequence.append(event)


	# has no effect other than appending a comment to the events list
	def add_comment_event(self, text: str) -> None:

		event = {'name': 'comment', 'text': text}

		self.events_sequence.append(event)
