import csv

def get_damage_rolls():

	def check_damage_rolls(character):
		for key, roll in damage_rolls[character].items():
			if roll not in possible_rolls[character]:
				if roll / 2 not in possible_rolls[character]:
					print(f'Invalid damage roll: {roll}')
				else:
					damage_rolls[character][key] = roll // 2

	damage_rolls = {}
	damage_rolls['auron'] = {}
	damage_rolls['tidus'] = {}
	possible_rolls = {}

	possible_rolls['tidus'] = (125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141)
	possible_rolls['auron'] = (260, 261, 262, 263, 264, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 278,
								279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 291, 292, 293, 294)

	# get damage rolls and check them
	damage_rolls_input = input('Damage rolls (Auron1 Tidus1 A2 T2 A3 T3): ')
	damage_rolls_input = damage_rolls_input.replace(',', ' ')
	damage_rolls_input = damage_rolls_input.replace('-', ' ')
	damage_rolls_input = damage_rolls_input.replace('/', ' ')
	damage_rolls_input = damage_rolls_input.replace('\\', ' ')

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
				return line, True, line_count
		line_count += 1
	return False, False, False


def get_ids_array(ids_file):
	ids_array = {}
	with open(ids_file) as ids:
		ids_file_reader = csv.reader(ids, delimiter=',')
		skip_line = True
		for line in ids_file_reader:

			if skip_line:
				skip_line = False
				continue

			ids_array[int(line[0])] = line[1]

	return ids_array


def get_characters_array(characters_file):
	with open(characters_file) as text_characters_file:
		text_characters_file_reader = csv.reader(text_characters_file, delimiter=',')
		text_characters_array = {}
		for line in text_characters_file_reader:
			text_characters_array[line[1]] = line[2]
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

			monster_name = ''
			for i in range(20):
				if line[408 + i] == '00': break
				monster_name += text_characters_array[line[408 + i]]

			monster_name = monster_name.lower().replace(' ', '_')

			monsters_list = monsters_array.keys()
			if f'{monster_name}_7' in monsters_list:
				monsters_array[f'{monster_name}_8'] = line
			elif f'{monster_name}_6' in monsters_list:
				monsters_array[f'{monster_name}_7'] = line
			elif f'{monster_name}_5' in monsters_list:
				monsters_array[f'{monster_name}_6'] = line
			elif f'{monster_name}_4' in monsters_list:
				monsters_array[f'{monster_name}_5'] = line
			elif f'{monster_name}_3' in monsters_list:
				monsters_array[f'{monster_name}_4'] = line
			elif f'{monster_name}_2' in monsters_list:
				monsters_array[f'{monster_name}_3'] = line
			elif monster_name in monsters_list:
				monsters_array[f'{monster_name}_2'] = line
			else: monsters_array[monster_name] = line

	return monsters_array


# gives a generator object
def get_rng_generator(seed_array):
	# first 6 values of the array are the seed damage rolls
	i = 6
	while True:
		yield int(seed_array[i])
		i += 1


# returns the prize struct byte array
def get_prize_struct(monster, monsters_array):
	monster = monster.lower().replace(' ', '_')
	# monster = ''.join([word[0].upper() + word[1:] for word in monster.split()])
	try:
		prize_struct = [int(value, 16) for value in monsters_array[monster]]
		return prize_struct
	except KeyError:
		return False


def get_item1(prize_struct, items_array):
	common_item, common_item_quantity = items_array[prize_struct[140]], prize_struct[148]
	rare_item, rare_item_quantity = items_array[prize_struct[142]], prize_struct[149]
	return f'{common_item} x{common_item_quantity} or {rare_item} x{rare_item_quantity}'


def get_item2(prize_struct, items_array):
	common_item, common_item_quantity = items_array[prize_struct[144]], prize_struct[150]
	rare_item, rare_item_quantity = items_array[prize_struct[146]], prize_struct[151]
	return f'{common_item} x{common_item_quantity} or {rare_item} x{rare_item_quantity}'


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

	def fix_out_of_bounds_value(value, lower_bound, higher_bound):
		if value < lower_bound:
			value = lower_bound
		if value > higher_bound:
			value = higher_bound
		return value

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
	# the first ability in the array is always 0 for armors, its either 0 or piercing/sensor (11/0) for weapons
	piercing_auto_ability_value = prize_struct[possible_auto_abilities_array_address] + (prize_struct[possible_auto_abilities_array_address + 1] * 256)

	equipment['abilities'] = {}

	# if the first ability is piercing it always gets added, only the case for auron and kimahri weapons
	if number_of_slots == 0 or piercing_auto_ability_value == 0:
		number_of_abilities_added = 0
	else:
		piercing_auto_ability_value -= 128 * 256
		equipment['ability_0_index'] = piercing_auto_ability_value
		equipment['abilities'][0] = abilities_array[piercing_auto_ability_value]
		number_of_abilities_added = 1

	if number_of_abilities_max > 0:
		current_dropped_equipment_ability = number_of_abilities_added

		while number_of_abilities_max > 0:

			# if all the slots are filled break
			if number_of_abilities_added >= number_of_slots: break

			# get a random ability, picks from ability 1 to ability 7, ability 0 is always piercing if present
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
						ability_to_check = equipment[f'ability_{current_equipment_slot}_index']
						if ability_to_check == ability_to_add:
							add_ability = False
							break
						number_of_checked_abilities += 1
						current_equipment_slot += 1

				# if the ability is not a duplicate add it to the current slot and advance both slot count and ability count
				if add_ability:
					equipment[f'ability_{current_dropped_equipment_ability}_index'] = ability_to_add
					equipment['abilities'][current_dropped_equipment_ability] = abilities_array[ability_to_add]
					number_of_abilities_added += 1
					current_dropped_equipment_ability += 1

			# always decrements
			number_of_abilities_max -= 1

	if number_of_abilities_added < 4:
		# null remaining ability slots, shouldnt be important, it never overwrites filled slots
		pass

	# delete 
	for i in range(number_of_slots - number_of_abilities_added):
		equipment['abilities'][number_of_abilities_added + 1 + i] = '-'

	return equipment


def get_spoils(prize_struct, abilities_array, items_array, characters_enabled_string, killer_index, rng_steal_drop, rng_equipment, rng_abilities):

	item1_dropped, item2_dropped, equipment_dropped = False, False, False
	item1, item2, equipment = False, False, False

	rng_item1 = next(rng_steal_drop)
	item1_drop_chance = prize_struct[136]
	if item1_drop_chance > (rng_item1 % 255):
		item1_dropped = True

	rng_item2 = next(rng_steal_drop)
	item2_drop_chance = prize_struct[137]
	if item2_drop_chance > (rng_item2 % 255):
		item2_dropped = True

	rng_equipment_drop = next(rng_steal_drop)
	equipment_drop_chance = prize_struct[139]
	if equipment_drop_chance > (rng_equipment_drop % 255):
		equipment_dropped = True

	if item1_dropped:
		item1 = get_item1(prize_struct, items_array)
	if item2_dropped:
		item2 = get_item2(prize_struct, items_array)
	if equipment_dropped:
		equipment = create_dropped_equipment(prize_struct, abilities_array, characters_enabled_string, killer_index, rng_equipment, rng_abilities)

	return item1, item2, equipment


def get_stolen_item(prize_struct, items_array, successful_steals, rng_steal_drop):
	rng_steal = next(rng_steal_drop)
	steal_chance = prize_struct[138] / (2 ** successful_steals)
	if steal_chance > (rng_steal % 255):
		common_item, common_item_quantity = items_array[prize_struct[164]], prize_struct[168]
		rare_item, rare_item_quantity = items_array[prize_struct[166]], prize_struct[169]
		return f'{common_item} x{common_item_quantity} or {rare_item} x{rare_item_quantity}'
	else: return 'failed'
