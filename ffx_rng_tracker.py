from get_spoils import *
import tkinter as tk
from tkinter import font


# needs ffxhd-raw-rng10-values.csv, ffxhd-raw-rng11-values.csv, ffxhd-raw-rng12-values.csv and ffxhd-raw-rng13-values.csv
# placed in the same folder to work

damage_rolls = get_damage_rolls()

current_steal_drop_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng10-values.csv', damage_rolls)
current_common_rare_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng11-values.csv', damage_rolls)
current_equipment_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng12-values.csv', damage_rolls)
current_abilities_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng13-values.csv', damage_rolls)

if seed_found:
	print('Seed found!')
	print(f'Seed number is {seed_number}')
else:
	print('Seed not found!')
	quit()

abilities_array = get_abilities_array(get_resource_path('files/ffxhd-abilities.csv'))
items_array = get_items_array(get_resource_path('files/ffxhd-items.csv'))
text_characters_array = get_characters_array(get_resource_path('files/ffxhd-characters.csv'))
monsters_array = get_monsters_array(get_resource_path('files/ffxhd-mon_data.csv'), text_characters_array)


def patch_monsters_array_for_hd(monsters_array):

	# 0 for weapon, 1 for armor
	def patch_abilities(monster_array, abilities_tuple, equipment_type=0):

		base_address = 178
		for character_index in range(7):
			character_offset = (equipment_type + (character_index * 2)) * 16
			for ability_slot in range(7):
				ability_slot_offset = (ability_slot + 1) * 2
				monster_array[base_address + character_offset + ability_slot_offset] = hex(abilities_tuple[ability_slot])

		return monster_array

	# droprates from 3% to 4%
	for monster in ['condor', 'dingo', 'water_flan', 'condor_2', 'dingo_2', 'water_flan_2',
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
		monsters_array[monster][139] = hex(12)

	# abilities
	# besaid
	monsters_array['dingo'] = patch_abilities(monsters_array['dingo'], (38, 42, 34, 30, 124, 124, 124))
	monsters_array['condor'] = patch_abilities(monsters_array['condor'], (0, 0, 0, 0, 126, 126, 126))
	monsters_array['water_flan'] = patch_abilities(monsters_array['water_flan'], (42, 42, 42, 42, 125, 125, 125))
	monsters_array['dingo_2'] = patch_abilities(monsters_array['dingo_2'], (38, 42, 34, 30, 124, 124, 124))
	monsters_array['condor_2'] = patch_abilities(monsters_array['condor_2'], (0, 0, 0, 0, 126, 126, 126))
	monsters_array['water_flan_2'] = patch_abilities(monsters_array['water_flan_2'], (42, 42, 42, 42, 125, 125, 125))

	# kilika
	# monsters_array['dinonix'] = patch_abilities(monsters_array['dinonix'], (126, 126, 126, 38, 38, 30, 42))
	# monsters_array['killer_bee'] = patch_abilities(monsters_array['killer_bee'], (126, 126, 126, 30, 34, 38, 42))
	# monsters_array['yellow_element'] = patch_abilities(monsters_array['yellow_element'], (38, 38, 38, 38, 125, 125, 125))

	# luca
	# monsters_array['raldo'] = patch_abilities(monsters_array['raldo'], (124, 124, 124, 30, 34, 38, 42))

	# mi'ihen
	# bomb
	# dual_horn
	# floating_eye
	# ipiria
	# mi'ihen_fang
	# monsters_array['raldo_2'] = patch_abilities(monsters_array['raldo_2'], (124, 124, 124, 30, 34, 38, 42))
	# monsters_array['vouivre_2'] = patch_abilities(monsters_array['vouivre_2'], (124, 124, 124, 30, 34, 38, 42))
	# monsters_array['white_element'] = patch_abilities(monsters_array['white_element'], (34, 34, 34, 34, 125, 125, 125))

	# mushroom rock road
	# monsters_array['gandarewa'] = patch_abilities(monsters_array['gandarewa'], (38, 38, 38, 38, 125, 125, 125))
	# monsters_array['lamashtu'] = patch_abilities(monsters_array['lamashtu'], (124, 124, 124, 30, 34, 38, 42))
	# monsters_array['raptor'] = patch_abilities(monsters_array['raptor'], (126, 126, 126, 38, 38, 30, 42))
	# monsters_array['red_element'] = patch_abilities(monsters_array['red_element'], (30, 30, 30, 30, 125, 125, 125))
	# monsters_array['thunder_flan'] = patch_abilities(monsters_array['thunder_flan'], (38, 38, 38, 38, 125, 125, 125))

	# djose highroad
	# bite_bug
	# monsters_array['bunyip'] = patch_abilities(monsters_array['bunyip'], (124, 124, 124, 30, 34, 38, 42))
	# garm
	# simurgh
	# snow_flan

	# moonflow
	# monsters_array['bunyip_2'] = patch_abilities(monsters_array['bunyip_2'], (124, 124, 124, 30, 34, 38, 42))

	# thunder plains
	# aerouge
	# monsters_array['buer'] = patch_abilities(monsters_array['buer'], (126, 126, 30, 34, 38, 42, 99))
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
	# monsters_array['evil_eye'] = patch_abilities(monsters_array['evil_eye'], (126, 126, 30, 34, 38, 42, 99))
	# monsters_array['ice_flan'] = patch_abilities(monsters_array['ice_flan'], (34, 34, 34, 34, 125, 125, 125))
	# monsters_array['mafdet'] = patch_abilities(monsters_array['mafdet'], (124, 124, 124, 30, 34, 38, 42))
	# monsters_array['snow_wolf'] = patch_abilities(monsters_array['snow_wolf'], (124, 124, 124, 30, 34, 38, 42))

	# bikanel
	# monsters_array['alcyone'] = patch_abilities(monsters_array['alcyone'], (0, 0, 0, 0, 126, 126, 126))
	# monsters_array['mushussu'] = patch_abilities(monsters_array['mushussu'], (124, 124, 124, 30, 34, 38, 42))
	# monsters_array['sand_wolf'] = patch_abilities(monsters_array['sand_wolf'], (124, 124, 124, 30, 34, 38, 42))

	# monsters_array['bomb_2'] = patch_abilities(monsters_array['bomb_2'], (30, 30, 30, 30, 30, 30, 124))
	# monsters_array['chimera_2'] = patch_abilities(monsters_array['chimera_2'], (103, 103, 103, 103, 104, 104, 125))
	# monsters_array['dual_horn_2'] = patch_abilities(monsters_array['dual_horn_2'], (67, 67, 67, 30, 30, 127, 127))
	# monsters_array['evil_eye_2'] = patch_abilities(monsters_array['evil_eye_2'], (126, 126, 30, 34, 38, 42, 99))

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
	# monsters_array['defender_x'] = patch_abilities(monsters_array['defender_x'], (99, 99, 99, 99, 99, 100, 124))

	# cavern of the stolen fayth
	# monsters_array['dark_element'] = patch_abilities(monsters_array['dark_element'], (125, 125, 125, 30, 30, 34, 42))
	# monsters_array['defender'] = patch_abilities(monsters_array['defender'], (99, 99, 99, 99, 98, 98, 124))
	# monsters_array['ghost'] = patch_abilities(monsters_array['ghost'], (103, 103, 103, 104, 104, 104, 125))
	# monsters_array['imp'] = patch_abilities(monsters_array['imp'], (38, 38, 38, 38, 125, 125, 125))
	# monsters_array['nidhogg'] = patch_abilities(monsters_array['nidhogg'], (124, 124, 124, 30, 34, 38, 42))
	# monsters_array['valaha'] = patch_abilities(monsters_array['valaha'], (67, 67, 67, 30, 30, 127, 127))
	# monsters_array['yowie'] = patch_abilities(monsters_array['yowie'], (126, 126, 126, 38, 38, 30, 42))


	return monsters_array


monsters_array = patch_monsters_array_for_hd(monsters_array)


def make_predictions(steal_drop_seed, common_rare_seed, equipment_seed, abilities_seed, abilities_array, items_array, monsters_array):


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


	def get_good_early_game_drops(abilities_to_test, characters_to_test, number_of_kills_range, number_of_steals_range):


		def get_good_equipment(enemy, characters_enabled_string, killer_index, abilities_to_test):
			prize_struct = get_prize_struct(enemy, monsters_array)
			if prize_struct[139] > (next(rng_steal_drop) % 255):
				equipment = create_dropped_equipment(prize_struct, abilities_array, characters_enabled_string, killer_index, rng_equipment, rng_abilities)
				if equipment['type'] == 'weapon' and equipment['character'] in characters_to_test:
					for i in range(4):
						try:
							# if the weapon has lightning- water- or ice-strike
							if equipment['abilities'][i] in abilities_to_test:
								return equipment
						except KeyError as error:
							return False

			return False


		good_early_game_drops = []

		for number_of_kills in range(number_of_kills_range[0] + 2, number_of_kills_range[1] + 2 + 1):

			for number_of_steals in range(number_of_steals_range[0], number_of_steals_range[1] + 1):

				# get all rng arrays
				rng_steal_drop = get_rng_generator(steal_drop_seed)
				rng_common_rare = get_rng_generator(common_rare_seed)
				rng_equipment = get_rng_generator(equipment_seed)
				rng_abilities = get_rng_generator(abilities_seed)

				# 15 kills before klikk
				for i in range((15 + number_of_kills) * 3):
					next(rng_steal_drop)

				for j in range(number_of_steals):
					next(rng_steal_drop)

				early_game_kills_tuple = (	('dingo', 'tywl', 0),
											('condor', 'tywl', 4),
											('water_flan', 'tywl', 5),
											('???', 'tywl', 0),
											('garuda_3', 'tywl', 7),
											('dingo_2', 'tywl', 0),
											('condor_2', 'tywl', 4),
											('water_flan_2', 'tywl', 5)
											)

				for enemy, characters_enabled_string, killer_index in early_game_kills_tuple:
					# roll for item1 and item2
					for k in range(2):
						next(rng_steal_drop)
					equipment = get_good_equipment(enemy, characters_enabled_string, killer_index, abilities_to_test)
					if equipment:
						good_early_game_drops.append({'enemy': enemy, 'number_of_piranhas': number_of_kills - 2, 
							'number_of_steals': number_of_steals, 'equipment': equipment})

		return good_early_game_drops


	for equipment_n, equipment_type in get_equipment_types().items():
		print(f'Equipment {"#" + str(equipment_n):>3}: {equipment_type}')

	abilities_to_test = ('Lightningstrike', 'Icestrike')
	characters_to_test = ('Tidus', 'Wakka')
	number_of_kills_range = (2, 14)
	number_of_steals_range = (2, 10)

	print(f'Testing all scenarios with {number_of_kills_range[0]}-{number_of_kills_range[1]} piranha kills and '
		f'{number_of_steals_range[0]}-{number_of_steals_range[1]} steals '
		f'for weapon drops for {"/".join(characters_to_test)} in Besaid '
		f'with at least 1 of these abilities: {", ".join(abilities_to_test)}')

	good_early_game_drops = get_good_early_game_drops(abilities_to_test, characters_to_test, number_of_kills_range, number_of_steals_range)

	# if the list is not empty
	if good_early_game_drops:
		for scenario in good_early_game_drops:
			print(f'Killing {scenario["number_of_piranhas"]} piranhas and stealing {scenario["number_of_steals"]} times, '
				f'{scenario["enemy"]} will drop {[ability for slot, ability in scenario["equipment"]["abilities"].items()]} for {scenario["equipment"]["character"]}')
	else: print(f'No weapons found')


make_predictions(current_steal_drop_seed, current_common_rare_seed, current_equipment_seed, current_abilities_seed,
				abilities_array, items_array, monsters_array)

quit()


def parse_notes(abilities_array, items_array, monsters_array, data_text):

	def highlight_pattern(text, pattern, tag, start='1.0', end='end', regexp=False):
		start = text.index(start)
		end = text.index(end)
		text.mark_set('matchStart', start)
		text.mark_set('matchEnd', start)
		text.mark_set('searchLimit', end)
		count = tk.IntVar()
		while True:
			index = text.search(pattern, 'matchEnd','searchLimit', count=count, regexp=regexp)
			if index == '': break
			if count.get() == 0: break # degenerate pattern which matches zero-length strings
			text.mark_set('matchStart', index)
			text.mark_set('matchEnd', f'{index}+{count.get()}c')
			text.tag_add(tag, 'matchStart', 'matchEnd')

	def get_equipment_counter():
		i = 0
		while True:
			i += 1
			yield i

	equipment_counter = get_equipment_counter()
	rng_steal_drop = get_rng_generator(current_steal_drop_seed)
	rng_common_rare = get_rng_generator(current_common_rare_seed)
	rng_equipment = get_rng_generator(current_equipment_seed)
	rng_abilities = get_rng_generator(current_abilities_seed)

	notes_lines_array = notes.get('1.0', 'end').split('\n')
	data = ''
	characters_enabled_string = 'ta'
	for line in notes_lines_array:
		if line != '':
			# fixes double spaces
			line = " ".join(line.split())

			if line[:3] == '///':
				data = ''
				continue

			if line[0] == '#':
				data += f'{line}\n'
				continue

			try:
				line = line.lower()
				event, params = [split for split in line.split(' ', 1)]

				if event == 'steal':
					monster, successful_steals = [split for split in params.split(' ', 1)]
					successful_steals = int(successful_steals)
					prize_struct = get_prize_struct(monster, monsters_array)
					if prize_struct == False:
						data += f'No monster named "{monster}"'
						next(rng_steal_drop)
						next(rng_common_rare)
					else:
						monster = monster.replace('_', ' ')
						monster = ' '.join([word[0].upper() + word[1:] for word in monster.split(' ')])
						data += f'Steal from {monster}: ' + get_stolen_item(prize_struct, items_array, successful_steals, rng_steal_drop, rng_common_rare)

				elif event == 'kill':
					monster, killer = [split for split in params.split(' ', 2)]

					killer_index = (	0 if killer.lower() == 'tidus' else 
										1 if killer.lower() == 'yuna' else 
										2 if killer.lower() == 'auron' else 
										3 if killer.lower() == 'kimahri' else 
										4 if killer.lower() == 'wakka' else 
										5 if killer.lower() == 'lulu' else 
										6 if killer.lower() == 'rikku' else 7
										)

					prize_struct = get_prize_struct(monster, monsters_array)

					if prize_struct == False:
						data += f'No monster named "{monster}"'

					else:
						item1, item2, equipment = get_spoils(prize_struct, abilities_array, items_array,
							characters_enabled_string, killer_index, rng_steal_drop, rng_common_rare, rng_equipment, rng_abilities)

						monster = monster.replace('_', ' ')
						monster = ' '.join([word[0].upper() + word[1:] for word in monster.split(' ')])

						data += f'{monster} drops: '

						if item1: data += f'{item1}'

						if item2: data += f', {item2}'

						if equipment:
							guaranteed_equipment = ' (guaranteed)' if equipment["guaranteed"] else '' 
							data += (	f', Equipment #{next(equipment_counter)}{guaranteed_equipment}: {equipment["type"]} for {equipment["character"]} '
										f'{[ability for slot, ability in equipment["abilities"].items()]} [{equipment["sell_gil_value"]} gil]')

						# if all 3 are False
						if any((item1, item2, equipment)) == False: data += 'No drops'

				elif event == 'death':
					data += 'Character death'
					next(rng_steal_drop)
					next(rng_steal_drop)
					next(rng_steal_drop)

				elif event == 'waste' or event == 'advance' or event == 'roll':
					rng, number_of_times = [split for split in params.split(' ', 1)]
					for i in range(int(number_of_times)):
						if rng == 'rng10': next(rng_steal_drop)
						elif rng == 'rng11': next(rng_common_rare)
						elif rng == 'rng12': next(rng_equipment)
						elif rng == 'rng13': next(rng_abilities)
					data += f'Advanced {rng} {number_of_times} times'

				elif event == 'party':
					characters_enabled_string = params.split(' ', 1)[0]
					data += 'Party changed'

				else: data += 'Invalid formatting'
			except ValueError as error:
				data += 'Invalid formatting'

		data += '\n'

	data = data[:-2]
	data_text.config(state='normal')
	data_text.delete(1.0,'end')
	data_text.insert(1.0, data)

	highlight_pattern(data_text, 'Equipment', 'equipment')
	highlight_pattern(data_text, 'No Encounters', 'no_encounters')
	highlight_pattern(data_text, '^#(.+?)?$', 'comment', regexp=True)
	highlight_pattern(data_text, '^Advanced rng.+$', 'rng_rolls', regexp=True)
	

	data_text.config(state='disabled')

	# on_notes_scroll(notes_scroll_position)
	data_text.yview('moveto', data_text_scroll_position)

# GUI
#--------------------------------------------------------------------------------------------------------------------------------------------------------------
root = tk.Tk()

def on_ui_close():
	global root
	root.quit()
	quit()

root.protocol('WM_DELETE_WINDOW', on_ui_close)
root.title('ffx_rng_tracker')
root.geometry('1368x800')

# Texts
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

texts_font = font.Font(family='Courier New', size=9)

data_text = tk.Text(root, font=texts_font, width=55)
data_text.pack(expand=True, fill='both', side='right')

data_text.tag_configure('equipment', foreground='#0000ff')
data_text.tag_configure('no_encounters', foreground='#00ff00')
data_text.tag_configure('comment', foreground='#888888')
data_text.tag_configure('rng_rolls', background='#ff0000')


notes = tk.Text(root, font=texts_font, width=43)
notes.pack(fill='y', side='left')

notes.bind('<KeyRelease>', lambda _: parse_notes(abilities_array, items_array, monsters_array, data_text))

data_text_scroll_position = 0.0


def on_data_text_scroll(*args):
	global data_text_scroll_position
	data_text_scroll_position = args[0]
	# notes.yview('moveto', args[0])


# notes_scroll_position = 0.0

# def on_notes_scroll(*args):
# 	global notes_scroll_position
# 	notes_scroll_position = args[0]
# 	data_text.yview('moveto', args[0])

data_text.configure(yscrollcommand=on_data_text_scroll)
# notes.configure(yscrollcommand=on_notes_scroll)

data_text.config(state='disabled')


def get_default_notes(default_notes_file):
	with open(default_notes_file) as notes_file:
		return notes_file.read()


try:
	default_notes = get_default_notes('ffxhd_rng_tracker_notes.txt')
except FileNotFoundError:
	default_notes = get_default_notes(get_resource_path('files/ffxhd_rng_tracker_default_notes.txt'))

notes.insert('end', default_notes)

parse_notes(abilities_array, items_array, monsters_array, data_text)

root.mainloop()

input('...')