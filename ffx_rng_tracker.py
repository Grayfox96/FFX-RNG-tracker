from get_spoils import *
import threading
import tkinter as tk
from tkinter import font


# needs ffxhd-raw-rng10-values.csv, ffxhd-raw-rng11-values.csv, ffxhd-raw-rng12-values.csv and ffxhd-raw-rng13-values.csv
# placed in the same folder to work

damage_rolls = get_damage_rolls()

current_steal_drop_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng10-values.csv', damage_rolls)
current_common_rare_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng11-values.csv', damage_rolls)
current_equipment_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng12-values.csv', damage_rolls)
current_abilities_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng13-values.csv', damage_rolls)

# current_seed_rng_array, seed_found, seed_number = get_current_seed('ffxhd-raw-rng-arrays.csv', damage_rolls)

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
				monster_array[base_address + character_offset + ability_slot_offset] = abilities_tuple[ability_slot]

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
		monsters_array[monster][139] = 12

	# abilities
	# besaid
	monsters_array['dingo'] = patch_abilities(monsters_array['dingo'], (38, 42, 34, 30, 124, 124, 124))
	monsters_array['condor'] = patch_abilities(monsters_array['condor'], (0, 0, 0, 0, 126, 126, 126))
	monsters_array['water_flan'] = patch_abilities(monsters_array['water_flan'], (42, 42, 42, 42, 125, 125, 125))
	monsters_array['dingo_2'] = patch_abilities(monsters_array['dingo_2'], (38, 42, 34, 30, 124, 124, 124))
	monsters_array['condor_2'] = patch_abilities(monsters_array['condor_2'], (0, 0, 0, 0, 126, 126, 126))
	monsters_array['water_flan_2'] = patch_abilities(monsters_array['water_flan_2'], (42, 42, 42, 42, 125, 125, 125))

	# kilika
	monsters_array['dinonix'] = patch_abilities(monsters_array['dinonix'], (38, 42, 38, 30, 126, 126, 126))
	monsters_array['killer_bee'] = patch_abilities(monsters_array['killer_bee'], (38, 42, 34, 30, 126, 126, 126))
	monsters_array['yellow_element'] = patch_abilities(monsters_array['yellow_element'], (38, 38, 38, 38, 125, 125, 125))

	# luca
	monsters_array['vouivre_2'] = patch_abilities(monsters_array['vouivre_2'], (38, 42, 34, 30, 124, 124, 124))

	# mi'ihen
	monsters_array['raldo_2'] = patch_abilities(monsters_array['raldo_2'], (38, 42, 34, 30, 124, 124, 124))
	# bomb
	# dual_horn
	# floating_eye
	# ipiria
	# mi'ihen_fang
	monsters_array['raldo'] = patch_abilities(monsters_array['raldo'], (38, 42, 34, 30, 124, 124, 124))
	monsters_array['vouivre'] = patch_abilities(monsters_array['vouivre'], (38, 42, 34, 30, 124, 124, 124))
	# white_element

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

	def event_steal(*params):
		if len(params) < 2:
			return 'Usage: steal [enemy_name] [successful steals]'
		elif len(params) >= 2:
			(monster, successful_steals) = params[:2]

		try:
			successful_steals = int(successful_steals)
		except ValueError:
			return f'Usage: steal [enemy_name] [successful steals (integer)]'

		prize_struct = get_prize_struct(monster, monsters_array)

		if prize_struct == False:
			return f'No monster named "{monster}"'
		else:
			monster = monster.replace('_', ' ')
			monster = ' '.join([word[0].upper() + word[1:] for word in monster.split(' ')])
			return f'Steal from {monster}: ' + get_stolen_item(prize_struct, items_array, successful_steals, rng_steal_drop, rng_common_rare)

	def event_kill(*params):

		if len(params) < 2:
			return 'Usage: kill [enemy_name] [killer]'
		elif len(params) >= 2:
			(monster, killer) = params[:2]

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
			return f'No monster named "{monster}"'

		else:
			item1, item2, equipment = get_spoils(prize_struct, abilities_array, items_array,
				characters_enabled_string, killer_index, rng_steal_drop, rng_common_rare, rng_equipment, rng_abilities)

			monster = monster.replace('_', ' ')
			monster = ' '.join([word[0].upper() + word[1:] for word in monster.split(' ')])

			result = f'{monster} drops: '

			if item1: result += f'{item1}'

			if item2: result += f', {item2}'

			if equipment:
				guaranteed_equipment = ' (guaranteed)' if equipment["guaranteed"] else '' 
				result += (	f', Equipment #{next(equipment_counter)}{guaranteed_equipment}: {equipment["type"]} for {equipment["character"]} '
					f'{[ability for slot, ability in equipment["abilities"].items()]} [{equipment["sell_gil_value"]} gil]')

			# if all 3 are False
			if any((item1, item2, equipment)) == False: result += 'No drops'

			return result

	def event_death(*params):
		for i in range(3):
			next(rng_steal_drop)

		return 'Character death'

	def event_roll(*params):
		if len(params) < 2:
			return 'Usage: waste/advance/roll [rng#] [amount]'
		if len(params) >= 2:
			(rng, number_of_times) = params[:2]

		for i in range(int(number_of_times)):
			if rng == 'rng10': next(rng_steal_drop)
			elif rng == 'rng11': next(rng_common_rare)
			elif rng == 'rng12': next(rng_equipment)
			elif rng == 'rng13': next(rng_abilities)
			else: return f'Can\'t advance {rng}'

		return f'Advanced {rng} {number_of_times} times'

	# aliases
	event_advance = event_roll
	event_waste = event_roll

	def event_party(*params):
		nonlocal characters_enabled_string

		valid_party_formations = ('ta', 't', 'tw', 'tywl', 'tykwl', 'tyakwl', 'tyakwlr', 'takwlr', 'ya', 'twr', 'tyawlr')

		if characters_enabled_string in valid_party_formations:
			characters_enabled_string = params[0]
			return f'Party changed to {characters_enabled_string}'
		else:
			return 'Invalid party formation'

	equipment_counter = get_equipment_counter()
	rng_steal_drop = get_rng_generator(current_steal_drop_seed)
	rng_common_rare = get_rng_generator(current_common_rare_seed)
	rng_equipment = get_rng_generator(current_equipment_seed)
	rng_abilities = get_rng_generator(current_abilities_seed)

	notes_lines_array = notes_text.get('1.0', 'end').split('\n')
	data = ''
	characters_enabled_string = 'ta'
	for line in notes_lines_array:
		if line != '':
			# fixes double spaces
			line = ' '.join(line.split())

			if line[:3] == '///':
				data = ''
				continue

			if line[0] == '#':
				data += f'{line}\n'
				continue

			try:
				line = line.lower()
				event, *params = [split for split in line.split(' ')]

				try:
					data += locals()['event_' + event](*params)
				except KeyError as error:
					# if event doesnt exists
					data += f'No event called {event}'

			except ValueError as error:
				data += 'Invalid formatting'

		data += '\n'

	# remove the last newline
	data = data[:-2]


	saved_position = data_scrollbar.get()
	data_text.config(state='normal', yscrollcommand=None)
	data_text.delete(1.0,'end')
	data_text.insert(1.0, data)

	highlight_pattern(data_text, 'Equipment', 'equipment')
	highlight_pattern(data_text, 'No Encounters', 'no_encounters')
	highlight_pattern(data_text, '^#(.+?)?$', 'comment', regexp=True)
	highlight_pattern(data_text, '^Advanced rng.+$', 'rng_rolls', regexp=True)
	for error_message in ('Invalid', 'No event called', 'Usage:', 'No monster named'):
		highlight_pattern(data_text, f'^{error_message}.+$', 'error', regexp=True)

	data_text.config(state='disabled', yscrollcommand=data_scrollbar.set)

	data_text.yview('moveto', saved_position[0])


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

# notes
# width in characters
notes_width = 40

notes_canvas = tk.Canvas(root, width=notes_width)
notes_canvas.pack(fill='y', side='left')

notes_text = tk.Text(notes_canvas, font=texts_font, width=notes_width)
notes_text.pack(fill='y', side='left')

notes_text.bind('<KeyRelease>', lambda _: parse_notes(abilities_array, items_array, monsters_array, data_text))

notes_scrollbar = tk.Scrollbar(notes_canvas)
notes_scrollbar.pack(fill='y', side='right')
notes_scrollbar.config(command=notes_text.yview)

notes_text.config(yscrollcommand=notes_scrollbar.set)

# data
data_canvas = tk.Canvas(root)
data_canvas.pack(expand=True, fill='both', side='right')

data_text = tk.Text(data_canvas, font=texts_font)
data_text.pack(expand=True, fill='both', side='left')

data_text.tag_configure('equipment', foreground='#0000ff')
data_text.tag_configure('no_encounters', foreground='#00ff00')
data_text.tag_configure('comment', foreground='#888888')
data_text.tag_configure('rng_rolls', foreground='#ff0000')
data_text.tag_configure('error', background='#ff0000')

data_scrollbar = tk.Scrollbar(data_canvas)
data_scrollbar.pack(fill='y', side='right')

data_scrollbar.config(command=data_text.yview)

data_text.configure(yscrollcommand=data_scrollbar.set)

data_text.config(state='disabled')


def get_default_notes(default_notes_file):
	with open(default_notes_file) as notes_file:
		return notes_file.read()


try:
	default_notes = get_default_notes('ffxhd_rng_tracker_notes.txt')
except FileNotFoundError:
	default_notes = get_default_notes(get_resource_path('files/ffxhd_rng_tracker_default_notes.txt'))

notes_text.insert('end', default_notes)

parse_notes(abilities_array, items_array, monsters_array, data_text)

make_predictions_thread = threading.Thread(target=make_predictions, args=(current_steal_drop_seed, current_common_rare_seed, current_equipment_seed, 
	current_abilities_seed, abilities_array, items_array, monsters_array), daemon=True)

# make_predictions(current_steal_drop_seed, current_common_rare_seed, current_equipment_seed, 
# 	current_abilities_seed, abilities_array, items_array, monsters_array)

make_predictions_thread.start()

root.mainloop()

input('...')