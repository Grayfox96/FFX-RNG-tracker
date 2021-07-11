from get_spoils import *
import tkinter as tk
from tkinter import font

damage_rolls = get_damage_rolls()

current_steal_drop_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng10-values.csv', damage_rolls)
# current_common_rare_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng11-values.csv', damage_rolls)
current_equipment_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng12-values.csv', damage_rolls)
current_abilities_seed, seed_found, seed_number = get_current_seed('ffxhd-raw-rng13-values.csv', damage_rolls)

if seed_found:
	print('Seed found!')
	print(f'Seed number is {seed_number}')
else:
	print('Seed not found!')
	quit()

abilities_array = get_ids_array('ffxhd-abilities.csv')
items_array = get_ids_array('ffxhd-items.csv')

text_characters_array = get_characters_array('ffxhd-characters.csv')

monsters_array = get_monsters_array('ffxhd-mon_data.csv', text_characters_array)

def parse_notes(abilities_array, items_array, monsters_array, data_text):

	rng_steal_drop = get_rng_generator(current_steal_drop_seed)
	# rng_common_rare = get_rng_generator(current_common_rare_seed)
	rng_equipment = get_rng_generator(current_equipment_seed)
	rng_abilities = get_rng_generator(current_abilities_seed)

	notes_lines_array = notes.get('1.0', 'end').split('\n')
	data = ''
	for line in notes_lines_array:
		if line != '':
			if line[0] == '#': continue
			try:
				line = line.lower()
				event, params = [split for split in line.split(' ', 1)]

				if event == 'steal':
					monster, successful_steals = [split for split in params.split(' ', 1)]
					successful_steals = int(successful_steals)
					prize_struct = get_prize_struct(monster, monsters_array)
					if prize_struct == False:
						data += 'Monster not in the database'
						next(rng_steal_drop)
					else: data += get_stolen_item(prize_struct, items_array, successful_steals, rng_steal_drop)

				elif event == 'kill':
					monster, killer, characters_enabled_string = [split for split in params.split(' ', 3)]

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
						data += 'Monster not in the database, if equipment drop -> waste rng12 4 + waste rng13 1'
						# roll rng10 3 times
						next(rng_steal_drop)
						next(rng_steal_drop)
						next(rng_steal_drop)

					else:
						item1, item2, equipment = get_spoils(prize_struct, abilities_array, items_array, characters_enabled_string, killer_index, rng_steal_drop, rng_equipment, rng_abilities)
						if item1 == False: item1 = 'no Item1'
						if item2 == False: item2 = 'no Item2'
						if equipment: data += f'{monster} drops: {item1}, {item2}, {equipment["type"]} for {equipment["character"]} {[ability for slot, ability in equipment["abilities"].items()]}'
						else: data += f'{monster} drops: {item1}, {item2}, no Equipment'

				elif event == 'death':
					data += 'Character death'
					next(rng_steal_drop)
					next(rng_steal_drop)
					next(rng_steal_drop)

				elif event == 'waste' or event == 'advance':
					rng, number_of_times = [split for split in params.split(' ', 1)]
					for i in range(int(number_of_times)):
						if rng == 'rng10':
							next(rng_steal_drop)
						elif rng == 'rng12':
							next(rng_equipment)
						elif rng == 'rng13':
							next(rng_abilities)
					data += f'{event}d {rng} {number_of_times} times'


				else: data += 'Invalid formatting'
			except ValueError as error:
				data += 'Invalid formatting'

		data += '\n'

	data = data[:-2]
	data_text.config(state='normal')
	data_text.delete(1.0,'end')
	data_text.insert(1.0, data)
	data_text.config(state='disabled')

# GUI
#--------------------------------------------------------------------------------------------------------------------------------------------------------------
root = tk.Tk()

def on_ui_close():
	global root
	root.quit()
	quit()

root.protocol('WM_DELETE_WINDOW', on_ui_close)
root.title('ffx_seed_finder')
root.geometry('1368x800')

# Texts
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

texts_font = font.Font(family='Courier New', size=9)

data_text = tk.Text(root, font=texts_font, width=55)
data_text.pack(expand=True, fill='both', side='right')
# data_text.insert('end', data)

notes = tk.Text(root, font=texts_font, width=43)
notes.pack(fill='y', side='left')

notes.bind('<KeyRelease>', lambda _: parse_notes(abilities_array, items_array, monsters_array, data_text))

# def on_data_text_scroll(*args):
# 	notes.yview('moveto', args[0])

# def on_notes_scroll(*args):
# 	data_text.yview('moveto', args[0])

# data_text.configure(yscrollcommand=on_data_text_scroll)
# notes.configure(yscrollcommand=on_notes_scroll)

data_text.config(state='disabled')


def get_default_notes(default_notes_file):
	with open(default_notes_file) as notes_file:
		return notes_file.read()

default_notes = get_default_notes('ffxhd_rng_tracker_default_notes.txt')

notes.insert('end', default_notes)

parse_notes(abilities_array, items_array, monsters_array, data_text)

root.mainloop()
