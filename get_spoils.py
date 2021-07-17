import csv
import sys
import os

def get_resource_path(relative_path):
	base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(base_path, relative_path)

def get_damage_rolls():

	def check_damage_rolls(character):
		for key, roll in damage_rolls[character].items():
			if roll not in possible_rolls[character]:
				if roll / 2 not in possible_rolls[character]:
					print(f'Invalid damage roll: {roll}')
				else:
					damage_rolls[character][key] = roll // 2

	damage_rolls = {'tidus': {}, 'auron': {}}

	possible_rolls = {	'tidus':(125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141),
						'auron':(260, 261, 262, 263, 264, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 278,
									279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 291, 292, 293, 294)
						}


	# get damage rolls and check them
	damage_rolls_input = input('Damage rolls (Auron1 Tidus1 A2 T2 A3 T3): ')

	# replace different symbols with spaces
	for symbol in (',', '-', '/', '\\'):
		damage_rolls_input = damage_rolls_input.replace(symbol, ' ')

	damage_rolls['auron'][1], damage_rolls['tidus'][1], damage_rolls['auron'][2], damage_rolls['tidus'][2], damage_rolls['auron'][3], \
		damage_rolls['tidus'][3] = [int(roll) for roll in damage_rolls_input.split()]

	for character in ['tidus', 'auron']:
		check_damage_rolls(character)

	return damage_rolls


# not useful for now
def get_number_of_dropped_equipment():
	for i in range(8):
		yield i
	while True:
		yield -1


# get rng seeds
def get_current_seed(rng_file, damage_rolls_dict):
	rng_file_reader = csv.reader(open(rng_file), delimiter=',')
	line_count = 0
	for line in rng_file_reader:
		if line_count == 0:
			pass
		else:
			if all([damage_rolls_dict['auron'][1] == int(line[0]), damage_rolls_dict['auron'][2] == int(line[2]), damage_rolls_dict['auron'][3] == int(line[4]),
					damage_rolls_dict['tidus'][1] == int(line[1]), damage_rolls_dict['tidus'][2] == int(line[3]), damage_rolls_dict['tidus'][3] == int(line[5])]):
				# first 6 values of the array are the seed damage rolls
				return line[6:], True, line_count
		line_count += 1
	return False, False, False


def get_abilities_array(abilities_file):
	abilities_array = {}
	with open(abilities_file) as abilities:
		abilities_file_reader = csv.reader(abilities, delimiter=',')
		skip_line = True
		for line in abilities_file_reader:

			if skip_line:
				skip_line = False
				continue

			abilities_array[int(line[0])] = {'name': line[1], 'gil_value': int(line[2])}

	return abilities_array


def get_items_array(items_file):
	items_array = {}
	with open(items_file) as items:
		items_file_reader = csv.reader(items, delimiter=',')
		skip_line = True
		for line in items_file_reader:

			if skip_line:
				skip_line = False
				continue

			items_array[int(line[0])] = line[1]

	return items_array


def get_characters_array(characters_file):
	with open(characters_file) as text_characters_file:
		text_characters_file_reader = csv.reader(text_characters_file, delimiter=',')
		skip_line = True
		text_characters_array = {}
		for line in text_characters_file_reader:

			if skip_line:
				skip_line = False
				continue

			text_characters_array[int(line[0])] = line[2]
	return text_characters_array


def get_monsters_array(monster_data, text_characters_array):
	with open(monster_data) as monster_data_file:
		monster_data_file_reader = csv.reader(monster_data_file, delimiter=',')
		skip_line = True
		monsters_array = {}
		for line in monster_data_file_reader:

			if skip_line:
				skip_line = False
				continue

			prize_struct = [int(value, 16) for value in line]

			monster_name = ''
			for i in range(20):
				if prize_struct[408 + i] == 0: break
				monster_name += text_characters_array[prize_struct[408 + i]]

			monster_name = monster_name.lower().replace(' ', '_')

			monsters_list = monsters_array.keys()
			if f'{monster_name}_7' in monsters_list:
				monsters_array[f'{monster_name}_8'] = prize_struct
			elif f'{monster_name}_6' in monsters_list:
				monsters_array[f'{monster_name}_7'] = prize_struct
			elif f'{monster_name}_5' in monsters_list:
				monsters_array[f'{monster_name}_6'] = prize_struct
			elif f'{monster_name}_4' in monsters_list:
				monsters_array[f'{monster_name}_5'] = prize_struct
			elif f'{monster_name}_3' in monsters_list:
				monsters_array[f'{monster_name}_4'] = prize_struct
			elif f'{monster_name}_2' in monsters_list:
				monsters_array[f'{monster_name}_3'] = prize_struct
			elif monster_name in monsters_list:
				monsters_array[f'{monster_name}_2'] = prize_struct
			else: monsters_array[monster_name] = prize_struct

	return monsters_array


# returns a generator object
def get_rng_generator(seed_array):

	i = 0

	while True:
		yield int(seed_array[i])
		i += 1

# returns a generator object
def get_rng_calculator_generator(rng_index, rng_initial_values):

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

	rng_value = int(rng_initial_values[rng_index])

	rng_constant_1 = s32(rng_constants_1[rng_index])

	rng_constant_2 = rng_constants_2[rng_index]

	while True:
		rng_value = s32(s32(rng_value) * rng_constant_1 ^ rng_constant_2)
		rng_value = s32((rng_value >> 0x10) + (rng_value << 0x10))
		yield rng_value & 0x7fffffff


# returns the prize struct byte array
def get_prize_struct(monster, monsters_array):
	monster = monster.lower().replace(' ', '_')
	# monster = ''.join([word[0].upper() + word[1:] for word in monster.split()])
	try:
		return monsters_array[monster]
	except KeyError:
		return False


def get_item1(prize_struct, items_array, item_common):
	if item_common:
		item, item_quantity = items_array[prize_struct[140]], prize_struct[148]
	else:
		item, item_quantity = items_array[prize_struct[142]], prize_struct[149]
	return f'{item} x{item_quantity}'


def get_item2(prize_struct, items_array, item_common):
	if item_common:
		item, item_quantity = items_array[prize_struct[144]], prize_struct[150]
	else:
		item, item_quantity = items_array[prize_struct[146]], prize_struct[151]
	return f'{item} x{item_quantity}'


def fix_out_of_bounds_value(value, lower_bound, higher_bound):
		if value < lower_bound:
			value = lower_bound
		if value > higher_bound:
			value = higher_bound
		return value


# uses rng12 and rng13 to generate an equipment drop from a specific enemy
def create_dropped_equipment(prize_struct, abilities_array, characters_enabled_string, killer_index, rng_equipment, rng_abilities):

	def get_characters_enabled(characters_enabled_string):
		characters_enabled_string = characters_enabled_string.lower()
		characters_enabled = [False, False, False, False, False, False, False]
		for character in characters_enabled_string:
			if character == 't': characters_enabled[0] = True
			elif character == 'y': characters_enabled[1] = True
			elif character == 'a': characters_enabled[2] = True
			elif character == 'k': characters_enabled[3] = True
			elif character == 'w': characters_enabled[4] = True
			elif character == 'l': characters_enabled[5] = True
			elif character == 'r': characters_enabled[6] = True
		return characters_enabled

	characters_enabled = get_characters_enabled(characters_enabled_string)

	equipment = {}

	# if number_of_dropped_equipment < 0:
	# 	return -1

	# dropped_equipment_array_offset = number_of_dropped_equipment * 22
	# base_dropped_equipment_address = 0
	# equipment['address'] = base_dropped_equipment_address + 254 + dropped_equipment_array_offset
	equipment['exists'] = 1
	equipment['enemy'] = ''

	# owner
	# a weapon for kimahri or auron might roll rng13 one less time since piercing gets always added as the first ability
	# so calculating both owner and equipment type is important
	party_member_index_loop = 0
	equipment_owner_base = 0

	# get number of party members enabled
	while party_member_index_loop < 7:
		is_party_member_enabled = characters_enabled[party_member_index_loop]
		if is_party_member_enabled != 0:
			equipment_owner_base += 1
		party_member_index_loop += 1

	if killer_index < 7:
		equipment_owner_base += 3
	else:
		killer_index = 0

	rng_equipment_owner = next(rng_equipment)
	number_of_enabled_party_members = 0
	party_member_index_loop = 0

	# get equipment owner
	while party_member_index_loop < 7:
		is_party_member_enabled = characters_enabled[party_member_index_loop]
		if is_party_member_enabled != 0:
			number_of_enabled_party_members += 1
			if (rng_equipment_owner % equipment_owner_base) < number_of_enabled_party_members:
				killer_index = party_member_index_loop
				break
		party_member_index_loop += 1

	equipment['character'] = (		'Tidus' if killer_index == 0 else 
									'Yuna' if killer_index == 1 else 
									'Auron' if killer_index == 2 else 
									'Kimahri' if killer_index == 3 else 
									'Wakka' if killer_index == 4 else 
									'Lulu' if killer_index == 5 else 
									'Rikku'
								)

	# type
	rng_weapon_or_armor = next(rng_equipment)
	equipment_type = rng_weapon_or_armor & 1
	equipment['type'] = 'weapon' if (equipment_type) == 0 else 'armor'

	# some misc values
	equipment['0_if_equipped'] = 255 # 255 not equipped, 0 equipped
	equipment['0x106'] = prize_struct[174] # ???
	equipment['base_weapon_damage'] = prize_struct[176] # base weapon damage, 16 or 18
	equipment['base_weapon_crit'] = prize_struct[175] # base weapon crit, 3-6-10

	# number of slots
	rng_number_of_slots = next(rng_equipment)
	number_of_slots_modifier = prize_struct[173] + (rng_number_of_slots & 7) - 4
	number_of_slots = fix_out_of_bounds_value(((number_of_slots_modifier + ((number_of_slots_modifier >> 31) & 3)) >> 2), 1, 4)
	equipment['slots'] = number_of_slots

	# number of abilities
	rng_number_of_abilities = next(rng_equipment)
	number_of_abilities_modifier = prize_struct[177] + (rng_number_of_abilities & 7) - 4
	number_of_abilities_max = (number_of_abilities_modifier + ((number_of_abilities_modifier >> 31) & 7)) >> 3

	# PossibleAutoAbilitiesArrayAddress = (ushort *)(TargetPrizeStructAddress + 0x32 + ((uint)*(byte *)(NumberOfDroppedEquipment + 0x103 + SomeAddress) + (uint)*(byte *)(NumberOfDroppedEquipment + 0x102 + SomeAddress) * 2) * 16);
	# weapon_or_armor = (uint)*(byte *)(NumberOfDroppedEquipment + 0x103 + SomeAddress)
	# killer_index = (uint)*(byte *)(NumberOfDroppedEquipment + 0x102 + SomeAddress)
	possible_auto_abilities_array_address = 178 + ((equipment_type + (killer_index * 2)) * 16)
	# the first ability in the array is always 0x0000 for armors, its either 0x0000 or piercing/sensor (0x800b/0x8000) for weapons
	forced_auto_ability_value = prize_struct[possible_auto_abilities_array_address] + (prize_struct[possible_auto_abilities_array_address + 1] * 256)

	equipment['abilities'] = {}
	equipment['abilities_index'] = {}
	equipment['base_gil_value'] = 0

	# if the first ability is piercing it always gets added, only the case for auron and kimahri weapons
	# weapons dropped from the kimahri boss enemy (???) always have sensor in the first slot so it gets added in the same way
	if number_of_slots == 0 or forced_auto_ability_value == 0:
		number_of_abilities_added = 0
	else:
		forced_auto_ability_value -= 128 * 256
		equipment['abilities_index'][0] = forced_auto_ability_value
		equipment['abilities'][0] = abilities_array[forced_auto_ability_value]['name']
		equipment['base_gil_value'] += abilities_array[forced_auto_ability_value]['gil_value']
		number_of_abilities_added = 1

	if number_of_abilities_max > 0:
		current_dropped_equipment_ability = number_of_abilities_added

		while number_of_abilities_max > 0:

			# if all the slots are filled break
			if number_of_abilities_added >= number_of_slots: break

			# get a random ability, picks from ability 1 to ability 7, ability 0 is always added without rng12 rolls if present
			rng_abilities_array_index = next(rng_abilities)
			ability_to_add = prize_struct[possible_auto_abilities_array_address + (((rng_abilities_array_index % 7) + 1) * 2)] + (prize_struct[possible_auto_abilities_array_address + (((rng_abilities_array_index % 7) + 1) * 2) + 1] * 256)
			add_ability = True

			# this checks for duplicate abilities
			if ability_to_add != 0:
				ability_to_add -= 128 * 256
				number_of_checked_abilities = 0
				if number_of_abilities_added > 0:
					current_equipment_slot = 0
					while number_of_abilities_added > number_of_checked_abilities:
						ability_to_check = equipment['abilities_index'][current_equipment_slot]
						if ability_to_check == ability_to_add:
							add_ability = False
							break
						number_of_checked_abilities += 1
						current_equipment_slot += 1

				# if the ability is not a duplicate add it to the current slot and advance both slot count and ability count
				if add_ability:
					equipment['abilities_index'][current_dropped_equipment_ability] = ability_to_add
					equipment['abilities'][current_dropped_equipment_ability] = abilities_array[ability_to_add]['name']
					equipment['base_gil_value'] += abilities_array[ability_to_add]['gil_value']
					number_of_abilities_added += 1
					current_dropped_equipment_ability += 1

			# always decrements
			number_of_abilities_max -= 1

	if number_of_abilities_added < 4:
		# null remaining ability slots, shouldnt be important, it never overwrites filled slots
		pass

	# delete nonexistent slots
	for i in range(number_of_slots - number_of_abilities_added):
		equipment['abilities'][number_of_abilities_added + 1 + i] = '-'

	# add other info
	# if enemy equipment droprate is 100%
	equipment['guaranteed'] = True if (prize_struct[139] == 255) else False

	# calculate buy and sell gil values
	slots_factor = (1, 1.5, 3, 5)
	empty_slots_factor = (1, 1, 1.5, 3, 400)
	equipment['gil_value'] = int((50 + equipment['base_gil_value']) * slots_factor[number_of_slots - 1] * empty_slots_factor[number_of_slots - number_of_abilities_added])
	equipment['sell_gil_value'] = equipment['gil_value'] // 4

	return equipment


def get_spoils(prize_struct, abilities_array, items_array, characters_enabled_string, killer_index, rng_steal_drop, rng_common_rare, rng_equipment, rng_abilities):

	item1, item2, equipment = False, False, False

	rng_item1 = next(rng_steal_drop)
	item1_drop_chance = prize_struct[136]
	if item1_drop_chance > (rng_item1 % 255):
		rng_item1_rarity = next(rng_common_rare)
		item1_common = False if ((rng_item1_rarity & 255) < 32) else True
		item1 = get_item1(prize_struct, items_array, item1_common)

	rng_item2 = next(rng_steal_drop)
	item2_drop_chance = prize_struct[137]
	if item2_drop_chance > (rng_item2 % 255):
		rng_item2_rarity = next(rng_common_rare)
		item2_common = False if ((rng_item2_rarity & 255) < 32) else True
		item2 = get_item2(prize_struct, items_array, item2_common)

	rng_equipment_drop = next(rng_steal_drop)
	equipment_drop_chance = prize_struct[139]
	if equipment_drop_chance > (rng_equipment_drop % 255):
		equipment = create_dropped_equipment(prize_struct, abilities_array, characters_enabled_string, killer_index, rng_equipment, rng_abilities)

	return item1, item2, equipment


def get_stolen_item(prize_struct, items_array, successful_steals, rng_steal_drop, rng_common_rare):
	rng_steal = next(rng_steal_drop)
	steal_chance = prize_struct[138] // (2 ** successful_steals)
	if steal_chance > (rng_steal % 255):
		rng_steal_rarity = next(rng_common_rare)
		item_common = False if ((rng_steal_rarity & 255) < 32) else True
		if item_common:
			item, item_quantity = items_array[prize_struct[164]], prize_struct[168]
		else:
			item, item_quantity = items_array[prize_struct[166]], prize_struct[169]
		return f'{item} x{item_quantity}'
	else: return 'failed'


def make_predictions(steal_drop_seed, common_rare_seed, equipment_seed, abilities_seed, abilities_array, items_array, monsters_array):

	def get_good_equipments(abilities_to_test, characters_to_test, number_of_kills_ranges, number_of_steals_range):

		def check_drops(enemy, characters_enabled_string, killer_index, kilika_in_kills=0, number_of_sinscales=0, kilika_out_kills=0):
			# roll for item1 and item2
			for k in range(2):
				next(rng_steal_drop)

			prize_struct = get_prize_struct(enemy, monsters_array)

			if prize_struct[139] > (next(rng_steal_drop) % 255):
				equipment = create_dropped_equipment(prize_struct, abilities_array, characters_enabled_string, killer_index, rng_equipment, rng_abilities)

				if equipment['type'] == 'weapon' and equipment['character'] in characters_to_test:
					for i in range(4):
						try:
							if equipment['abilities'][i] in abilities_to_test:

								good_equipment = {'enemy': enemy, 'number_of_piranhas': number_of_piranha_kills - 4, 
									'number_of_steals': number_of_steals, 'equipment': equipment, 'killer_index': killer_index, 
									'kilika_in_kills': kilika_in_kills, 'number_of_sinscales': number_of_sinscales, 
									'kilika_out_kills': kilika_out_kills}

								if good_equipment not in good_equipments:
									good_equipments.append(good_equipment)

						except KeyError as error:
							pass

		good_equipments = []

		# check for every possible number of steals
		for number_of_steals in range(number_of_steals_range[0], number_of_steals_range[1] + 1):
			# check every possible number of piranha kills + klikk and tros
			for number_of_piranha_kills in range(number_of_kills_ranges['piranhas'][0] + 4, number_of_kills_ranges['piranhas'][1] + 4 + 1):
				# check for kilika possible equipments to be from these enemies
				kilika_enemies = ('killer_bee', 'dinonix', 'yellow_element')
				for kilika_enemy in kilika_enemies:

					# get the possible killers based on the enemy
					if kilika_enemy == 'killer_bee':		kilika_killers = (4, 7)
					elif kilika_enemy == 'dinonix':			kilika_killers = (0, 4, 7)
					elif kilika_enemy == 'yellow_element':	kilika_killers = (7,)
					else:									kilika_killers = (0, 4, 7)

					# check for kilika kills
					for kilika_killer in kilika_killers:
						for number_of_sinscales in (2, 4):
							# check for every possible number of kills before geneaux
							for kilika_in_kills in range(number_of_kills_ranges['kilika_in'][0], number_of_kills_ranges['kilika_in'][1] + 1):

								# check for every possible number of kills after geneaux
								for kilika_out_kills in range(number_of_kills_ranges['kilika_out'][0], number_of_kills_ranges['kilika_out'][1] + 1):

									# get all rng arrays
									rng_steal_drop = get_rng_generator(steal_drop_seed)
									rng_common_rare = get_rng_generator(common_rare_seed)
									rng_equipment = get_rng_generator(equipment_seed)
									rng_abilities = get_rng_generator(abilities_seed)

									# 15 kills before klikk
									for i in range((15 + number_of_piranha_kills) * 3):
										next(rng_steal_drop)

									for i in range(number_of_steals):
										next(rng_steal_drop)

									besaid_forced_kills = (	('dingo', 'tywl', 0),
															('condor', 'tywl', 4),
															('water_flan', 'tywl', 5),
															('???', 'tywl', 0),
															('garuda_3', 'tywl', 7),
															('dingo_2', 'tywl', 0),
															('condor_2', 'tywl', 4),
															('water_flan_2', 'tywl', 5)
															)

									for enemy, characters_enabled_string, killer_index in besaid_forced_kills:
										check_drops(enemy, characters_enabled_string, killer_index)

									boat_kilika_forced_kills = (	('sin', 'tykwl', 7),
																	('sinspawn_echuilles', 'tykwl', 0),
																	('ragora_2', 'tykwl', 0)
																	)

									for enemy, characters_enabled_string, killer_index in boat_kilika_forced_kills:
										check_drops(enemy, characters_enabled_string, killer_index)

									for i in range(kilika_in_kills):
										check_drops(kilika_enemy, 'tykwl', kilika_killer, kilika_in_kills)

									kilika_forced_kills = (	("geneaux's_tentacle", 'tykwl', 7),
															("geneaux's_tentacle", 'tykwl', 7),
															('sinspawn_geneaux', 'tykwl', 7)
															)

									for enemy, characters_enabled_string, killer_index in kilika_forced_kills:
										check_drops(enemy, characters_enabled_string, killer_index, kilika_in_kills)

									for i in range(kilika_out_kills):

										# at least 4 kills in kilika
										if kilika_out_kills + kilika_in_kills < 4:
											kilika_out_kills = 4 - kilika_in_kills

										check_drops(kilika_enemy, 'tykwl', kilika_killer, kilika_in_kills, number_of_sinscales, kilika_out_kills)

									luca_forced_kills = (	('Worker', 'tykwl', 5),
															('Worker', 'tykwl', 5),
															('Worker', 'tykwl', 5),
															('Worker', 'tykwl', 5),
															('Worker', 'tykwl', 5),
															('Worker', 'tykwl', 3),
															('Worker', 'tykwl', 5),
															('Worker', 'tykwl', 5),
															('Worker', 'tykwl', 5),
															('Worker', 'tykwl', 0),
															('Oblitzerator', 'tykwl', 0)
															)

									for enemy, characters_enabled_string, killer_index in luca_forced_kills:
										check_drops(enemy, characters_enabled_string, killer_index, kilika_in_kills, number_of_sinscales, kilika_out_kills)

									# sahagin chiefs
									for i in range(17 * 3):
										next(rng_steal_drop)

									luca_miihen_forced_kills = (	('Vouivre_2', 'tyakwl', 2),
																	('Garuda_2', 'tyakwl', 2),
																	('Raldo_2', 'tyakwl', 2),
																	)

									for enemy, characters_enabled_string, killer_index in luca_miihen_forced_kills:
										check_drops(enemy, characters_enabled_string, killer_index, kilika_in_kills, number_of_sinscales, kilika_out_kills)

		return good_equipments

	def get_equipment_types():
		rng_equipment = get_rng_generator(equipment_seed)
		equipment_types = {}
		for i in range(40):
			next(rng_equipment)

			rng_weapon_or_armor = next(rng_equipment)
			equipment_type = rng_weapon_or_armor & 1
			equipment_type = 'weapon' if (equipment_type) == 0 else 'armor'

			next(rng_equipment)
			next(rng_equipment)

			equipment_types[i + 1] = equipment_type

		return equipment_types

	abilities_to_test = ('Lightningstrike', 'Icestrike')
	characters_to_test = ('Tidus', 'Wakka')
	number_of_kills_ranges = {'piranhas': (0, 6), 'kilika_in': (2, 7),'kilika_out': (0, 6)}
	number_of_steals_range = (4, 9)

	print(
		f'Testing all scenarios with '
		f'{number_of_steals_range[0]}-{number_of_steals_range[1]} steals, '
		f'{number_of_kills_ranges["piranhas"][0]}-{number_of_kills_ranges["piranhas"][1]} optional piranha kills, '
		f'2-4 Sinscales kills, '
		f'{number_of_kills_ranges["kilika_in"][0]}-{number_of_kills_ranges["kilika_in"][1]} Kilika(In) kills, '
		f'{number_of_kills_ranges["kilika_out"][0]}-{number_of_kills_ranges["kilika_out"][1]} Kilika(Out) kills, '
		f'for weapon drops for {"/".join(characters_to_test)} in Besaid, Kilika and Luca '
		f'with at least 1 of these abilities: {", ".join(abilities_to_test)}'
		)

	good_equipments = get_good_equipments(abilities_to_test, characters_to_test, number_of_kills_ranges, number_of_steals_range)

	# if the list is not empty
	if good_equipments:
		output = '------------------------------------------------------------------------------------------------------------------------\n'
		output += 'Steals | Piranhas | Sinscales | Kilika In | Kilika Out |          Enemy |  Killer | Owner | Abilities\n'
		output += '------------------------------------------------------------------------------------------------------------------------\n'
		for scenario in good_equipments:

			scenario['killer'] = (	'Tidus' if scenario['killer_index'] == 0 else 
									'Yuna' if scenario['killer_index'] == 1 else 
									'Auron' if scenario['killer_index'] == 2 else 
									'Kimahri' if scenario['killer_index'] == 3 else 
									'Wakka' if scenario['killer_index'] == 4 else 
									'Lulu' if scenario['killer_index'] == 5 else 
									'Rikku' if scenario['killer_index'] == 6 else 
									'Valefor'  if scenario['killer_index'] == 7 else 
									'???'
									)

			output += f'{scenario["number_of_steals"]:>6} | {scenario["number_of_piranhas"]:>8} | '
			output += f'{scenario["number_of_sinscales"]:>9} | '
			output += f'{scenario["kilika_in_kills"]:>9} | '
			output += f'{scenario["kilika_out_kills"]:>10} | '
			output += f'{scenario["enemy"]:>14} | {scenario["killer"]:>7} | {scenario["equipment"]["character"]:>5} | '
			output += f'{", ".join([ability for slot, ability in scenario["equipment"]["abilities"].items()])}\n'

		output += '------------------------------------------------------------------------------------------------------------------------'
		print(output)

	else: print(f'No weapons found')

	for equipment_n, equipment_type in get_equipment_types().items():
		print(f'Equipment {"#" + str(equipment_n):>3}: {equipment_type}')
