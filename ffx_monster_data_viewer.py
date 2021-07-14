from get_spoils import *
import tkinter as tk
from tkinter import font


def print_monster_data(monster_index, items_array, monsters_array, monster_names_list, monster_data_text):

	try:
		monster_index = monster_index[0]
	except IndexError:
		return

	prize_struct = get_prize_struct(monster_names_list[monster_index], monsters_array)

	monster_data = monster_names_list[monster_index] + '\n'

	monster_data += f'HP = {(prize_struct[23] * 256 * 256 * 256) + (prize_struct[22] * 256 * 256) + (prize_struct[21] * 256) + prize_struct[20]}\n'
	monster_data += f'MP = {(prize_struct[27] * 256 * 256 * 256) + (prize_struct[26] * 256 * 256) + (prize_struct[25] * 256) + prize_struct[24]}\n'
	monster_data += f'Overkill threshold = {(prize_struct[31] * 256 * 256 * 256) + (prize_struct[30] * 256 * 256) + (prize_struct[29] * 256) + prize_struct[28]}\n'
	monster_data += f'Strength = {prize_struct[32]}\n'
	monster_data += f'Defense = {prize_struct[33]}\n'
	monster_data += f'Magic = {prize_struct[34]}\n'
	monster_data += f'Magic Defense = {prize_struct[35]}\n'
	monster_data += f'Agility = {prize_struct[36]}\n'
	monster_data += f'Luck = {prize_struct[37]}\n'
	monster_data += f'Evasion = {prize_struct[38]}\n'
	monster_data += f'Accuracy = {prize_struct[39]}\n'
	monster_data += f'\n'

	monster_data += f'Gil = {(prize_struct[129] * 256) + prize_struct[128]}\n'
	monster_data += f'Regular AP = {(prize_struct[131] * 256) + prize_struct[130]}\n'
	monster_data += f'Overkill AP = {(prize_struct[133] * 256) + prize_struct[132]}\n'
	# monster_data += f'??? = {(prize_struct[135] * 256) + prize_struct[134]}\n'
	monster_data += f'\n'

	monster_data += f'Item 1 drop chance = {prize_struct[136]}/255\n'
	monster_data += f'Item 2 drop chance = {prize_struct[137]}/255\n'
	monster_data += f'Base steal chance = {prize_struct[138]}/255\n'
	monster_data += f'Equipment drop chance = {prize_struct[139]}/255\n'
	monster_data += f'\n'

	# items
	for i in range(4):
		if i == 0: monster_data += f'Common Item 1 drop = '
		elif i == 1: monster_data += f'Rare Item 1 drop = '
		elif i == 2: monster_data += f'Common Item 2 drop = '
		elif i == 3: monster_data += f'Rare Item 2 drop = '

		if prize_struct[141 + (i * 2)] == 32:
			monster_data += f'{items_array[prize_struct[140 + (i * 2)]]} x{prize_struct[148 + i]}\n'
		else: monster_data += f'Nothing\n'

	monster_data += f'\n'

	# overkill items
	for i in range(4):
		if i == 0: monster_data += f'Overkill Common Item 1 drop = '
		elif i == 1: monster_data += f'Overkill Rare Item 1 drop = '
		elif i == 2: monster_data += f'Overkill Common Item 2 drop = '
		elif i == 3: monster_data += f'Overkill Rare Item 2 drop = '

		if prize_struct[153 + (i * 2)] == 32:
			monster_data += f'{items_array[prize_struct[152 + (i * 2)]]} x{prize_struct[160 + i]}\n'
		else: monster_data += f'Nothing\n'

	# steal
	if prize_struct[165] == 32:
		monster_data += f'Common Steal: {items_array[prize_struct[164]]} x{prize_struct[168]}\n'
	else: monster_data += f'Common Steal: Nothing\n'

	if prize_struct[167] == 32:
		monster_data += f'Rare Steal: {items_array[prize_struct[166]]} x{prize_struct[169]}\n'
	else: monster_data += f'Rare Steal: Nothing\n'

	monster_data += f'\n'

	# bribe
	if prize_struct[171] == 32:
		monster_data += f'Bribe drop: {items_array[prize_struct[170]]} x{prize_struct[172]}(max)\n'
	else: monster_data += f'Bribe drop: Nothing\n'

	monster_data += f'\n'

	# equipment information
	if prize_struct[174] == 1:
		number_of_slots_modifier_min = prize_struct[173] + 0 - 4
		number_of_slots_modifier_max = prize_struct[173] + 7 - 4
		number_of_slots_min = fix_out_of_bounds_value(((number_of_slots_modifier_min + ((number_of_slots_modifier_min >> 31) & 3)) >> 2), 1, 4)
		number_of_slots_max = fix_out_of_bounds_value(((number_of_slots_modifier_max + ((number_of_slots_modifier_max >> 31) & 3)) >> 2), 1, 4)
		monster_data += f'Number of equipment slots range: {number_of_slots_min}-{number_of_slots_max}\n'

		monster_data += f'Equipment additional crit chance: {prize_struct[175]}\n'
		monster_data += f'Weapon damage multiplier: {prize_struct[176]}\n'

		number_of_abilities_modifier_min = prize_struct[177] + 0 - 4
		number_of_abilities_modifier_max = prize_struct[177] + 7 - 4
		number_of_abilities_max_min = (number_of_abilities_modifier_min + ((number_of_abilities_modifier_min >> 31) & 7)) >> 3
		number_of_abilities_max_max = (number_of_abilities_modifier_max + ((number_of_abilities_modifier_max >> 31) & 7)) >> 3

		monster_data += f'Number of abilities range: {number_of_abilities_max_min}-{number_of_abilities_max_max}\n'
	else: monster_data += f'No equipment drops\n\n\n\n'

	# print raw data
	byte_index = 0
	monster_data += '\n' + ' '.join([f'[{hex(byte_index + i)[2:]:>3}]' for i in range(16)]) + '\n'

	for byte in prize_struct:
		monster_data += f' {byte:>3}  '
		# sections
		if byte_index == 0x80 - 1: monster_data += '\nPrize struct'
		elif byte_index == 0xB0 - 1: monster_data += '\n             start of equipment'
		elif byte_index == 0x190 - 1: monster_data += '\n             end of equipment'
		# every 16 bytes make a new line
		if byte_index % 16 == 15:
			monster_data += '\n' + ' '.join([f'[{hex(byte_index + i + 1)[2:]:>3}]' for i in range(16)]) + '\n'
		byte_index += 1

	monster_data_text.config(state='normal')
	monster_data_text.delete(1.0,'end')
	monster_data_text.insert(1.0, monster_data)
	monster_data_text.config(state='disabled')


items_array = get_ids_array(get_resource_path('files/ffxhd-items.csv'))
text_characters_array = get_characters_array(get_resource_path('files/ffxhd-characters.csv'))
monsters_array = get_monsters_array(get_resource_path('files/ffxhd-mon_data.csv'), text_characters_array)
monster_names_list = sorted(list(monsters_array.keys()))

# GUI
#--------------------------------------------------------------------------------------------------------------------------------------------------------------
root = tk.Tk()

def on_ui_close():
	global root
	root.quit()
	quit()

root.protocol('WM_DELETE_WINDOW', on_ui_close)
root.title('ffx_monster_data_viewer')
root.geometry('1000x800')

# Texts
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

texts_font = font.Font(family='Courier New', size=9)

monster_data_text = tk.Text(root, font=texts_font, width=55)
monster_data_text.pack(expand=True, fill='both', side='right')

monsters_listbox_var = tk.StringVar(value=monster_names_list)
monsters_listbox = tk.Listbox(root, width=30, height=800, listvariable=monsters_listbox_var)
monsters_listbox.bind("<<ListboxSelect>>", lambda _: print_monster_data(monsters_listbox.curselection(), items_array, monsters_array, monster_names_list, monster_data_text))
monsters_listbox.pack(fill='y', side='left')

root.mainloop()

input('...')
