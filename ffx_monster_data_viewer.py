import ffx_rng_tracker
import tkinter as tk
from tkinter import font


class FFXInfo(ffx_rng_tracker.FFXRNGTracker):

    def __init__(self) -> None:
        self.abilities = self.get_ability_names('files/ffxhd-abilities.csv')
        self.items = self.get_item_names('files/ffxhd-items.csv')
        self.text_characters = self.get_text_characters(
            'files/ffxhd-characters.csv')
        self.monsters_data = self.get_monsters_data(
            'files/ffxhd-mon_data.csv')

        self._patch_monsters_dict_for_hd()


def print_monster_data(monster_index, monster_data_text):

    def add_bytes(address: int, length: int) -> int:
        '''Adds the value of adjacent bytes in a prize struct.'''
        value = 0
        for i in range(length):
            value += prize_struct[address + i] * (256 ** i)
        return value

    def get_elements(address: int) -> str:
        output = []
        if prize_struct[address] & 0b00001:
            output.append('Fire')
        if prize_struct[address] & 0b00010:
            output.append('Ice')
        if prize_struct[address] & 0b00100:
            output.append('Thunder')
        if prize_struct[address] & 0b01000:
            output.append('Water')
        if prize_struct[address] & 0b10000:
            output.append('Holy')
        if output == []:
            return 'Nothing'
        else:
            return '/'.join(output)

    try:
        monster_index = monster_index[0]
    except IndexError:
        return

    prize_struct = ffx_info.monsters_data[monster_names[monster_index]]

    monster_data = monster_names[monster_index] + '\n'
    # stats
    monster_data += f'HP = {add_bytes(20, 4)}\n'
    monster_data += f'MP = {add_bytes(24, 4)}\n'
    monster_data += f'Overkill threshold = {add_bytes(28, 4)}\n'
    monster_data += f'Strength = {prize_struct[32]}\n'
    monster_data += f'Defense = {prize_struct[33]}\n'
    monster_data += f'Magic = {prize_struct[34]}\n'
    monster_data += f'Magic Defense = {prize_struct[35]}\n'
    monster_data += f'Agility = {prize_struct[36]}\n'
    monster_data += f'Luck = {prize_struct[37]}\n'
    monster_data += f'Evasion = {prize_struct[38]}\n'
    monster_data += f'Accuracy = {prize_struct[39]}\n'
    monster_data += '\n'
    # elemental affinities
    monster_data += f'Absorbs: {get_elements(43)}\n'
    monster_data += f'Is immune to: {get_elements(44)}\n'
    monster_data += f'Halves: {get_elements(45)}\n'
    monster_data += f'Is weak to: {get_elements(46)}\n'
    monster_data += '\n'
    # loot
    monster_data += f'Gil = {add_bytes(128, 2)}\n'
    monster_data += f'Regular AP = {add_bytes(130, 2)}\n'
    monster_data += f'Overkill AP = {add_bytes(132, 2)}\n'
    # monster_data += f'??? = {add_bytes(134, 2)}\n'
    monster_data += '\n'
    monster_data += f'Item 1 drop chance = {prize_struct[136]}/255\n'
    monster_data += f'Item 2 drop chance = {prize_struct[137]}/255\n'
    monster_data += f'Base steal chance = {prize_struct[138]}/255\n'
    monster_data += f'Equipment drop chance = {prize_struct[139]}/255\n'
    monster_data += '\n'
    # items
    for i in range(4):
        if i == 0:
            monster_data += 'Common Item 1 drop = '
        elif i == 1:
            monster_data += 'Rare Item 1 drop = '
        elif i == 2:
            monster_data += 'Common Item 2 drop = '
        elif i == 3:
            monster_data += 'Rare Item 2 drop = '
        # check if the item is not actually null
        if prize_struct[141 + (i * 2)] == 32:
            item_name = ffx_info.items[prize_struct[140 + (i * 2)]]
            item_quantity = prize_struct[148 + i]
            monster_data += f'{item_name} x{item_quantity}\n'
        else:
            monster_data += 'Nothing\n'
    monster_data += '\n'
    # overkill items
    for i in range(4):
        if i == 0:
            monster_data += 'Overkill Common Item 1 drop = '
        elif i == 1:
            monster_data += 'Overkill Rare Item 1 drop = '
        elif i == 2:
            monster_data += 'Overkill Common Item 2 drop = '
        elif i == 3:
            monster_data += 'Overkill Rare Item 2 drop = '
        if prize_struct[153 + (i * 2)] == 32:
            item_name = ffx_info.items[prize_struct[152 + (i * 2)]]
            item_quantity = prize_struct[160 + i]
            monster_data += f'{item_name} x{item_quantity}\n'
        else:
            monster_data += 'Nothing\n'
    monster_data += '\n'
    # steal
    if prize_struct[165] == 32:
        item_name = ffx_info.items[prize_struct[164]]
        item_quantity = prize_struct[168]
        monster_data += (f'Common Steal: {item_name} x{item_quantity}\n')
    else:
        monster_data += 'Common Steal: Nothing\n'
    if prize_struct[167] == 32:
        item_name = ffx_info.items[prize_struct[166]]
        item_quantity = prize_struct[169]
        monster_data += (f'Rare Steal: {item_name} x{item_quantity}\n')
    else:
        monster_data += 'Rare Steal: Nothing\n'
    monster_data += '\n'
    # bribe
    if prize_struct[171] == 32:
        item_name = ffx_info.items[prize_struct[170]]
        item_quantity = prize_struct[172]
        monster_data += (f'Bribe drop: {item_name} x{item_quantity}(max)\n')
    else:
        monster_data += 'Bribe drop: Nothing\n'
    monster_data += '\n'
    # status resistances
    monster_data += 'Status resistances:\n'
    monster_data += f'death:        {prize_struct[47]:>3} | '
    monster_data += f'zombie:       {prize_struct[48]:>3} | '
    monster_data += f'petrify:      {prize_struct[49]:>3} | '
    monster_data += f'poison:       {prize_struct[50]:>3} | '
    monster_data += f'power break:  {prize_struct[51]:>3}\n'
    monster_data += f'magic break:  {prize_struct[52]:>3} | '
    monster_data += f'armor break:  {prize_struct[53]:>3} | '
    monster_data += f'mental break: {prize_struct[54]:>3} | '
    monster_data += f'confuse:      {prize_struct[55]:>3} | '
    monster_data += f'berserk:      {prize_struct[56]:>3}\n'
    monster_data += f'provoke:      {prize_struct[57]:>3} | '
    monster_data += f'threaten:     {prize_struct[58]:>3} | '
    monster_data += f'sleep:        {prize_struct[59]:>3} | '
    monster_data += f'silence:      {prize_struct[60]:>3} | '
    monster_data += f'dark:         {prize_struct[61]:>3}\n'
    monster_data += f'protect:      {prize_struct[62]:>3} | '
    monster_data += f'shell:        {prize_struct[63]:>3} | '
    monster_data += f'reflect:      {prize_struct[64]:>3} | '
    monster_data += f'nulblaze:     {prize_struct[65]:>3} | '
    monster_data += f'nulfrost:     {prize_struct[66]:>3}\n'
    monster_data += f'nulshock:     {prize_struct[67]:>3} | '
    monster_data += f'nultide:      {prize_struct[68]:>3} | '
    monster_data += f'regen:        {prize_struct[69]:>3} | '
    monster_data += f'haste:        {prize_struct[70]:>3} | '
    monster_data += f'slow:         {prize_struct[71]:>3}\n'
    monster_data += '\n'
    # other status information
    monster_data += f'undead?: {prize_struct[72]}\n'
    # monster_data += f'always 0: {prize_struct[73]}\n'
    monster_data += ('auto-status (32=reflect, 192=nulall, 224=both): '
                     f'{prize_struct[74]}\n')
    monster_data += ('auto-status (3=???, 4=regen, 7=both): '
                     f'{prize_struct[75]}\n')
    monster_data += '\n'
    # equipment information
    # check if the monster can drop equipment
    if prize_struct[174] == 1:
        monster_data += ('Equipment additional crit chance: '
                         f'{prize_struct[175]}\n')
        monster_data += f'Weapon damage multiplier: {prize_struct[176]}\n'
        # get the number of slots spread
        monster_data += 'Number of equipment slots spread: '
        slots_spread = []
        for i in range(8):
            slots_mod = prize_struct[173] + i - 4
            slots = ((slots_mod + ((slots_mod >> 31) & 3)) >> 2)
            slots = ffx_info._fix_out_of_bounds_value(slots)
            slots_spread.append(str(slots))
        monster_data += f'{" - ".join(slots_spread)}\n'
        # get the number of abilities spread
        abilities_spread = []
        monster_data += 'Number of abilities spread:       '
        for i in range(8):
            abilities_mod = prize_struct[177] + i - 4
            abilities_max = (abilities_mod + ((abilities_mod >> 31) & 7)) >> 3
            abilities_spread.append(str(abilities_max))
        monster_data += f'{" - ".join(abilities_spread)}\n'
        monster_data += '\n'
        # equipment abilities
        monster_data += '         Forced ability    '
        monster_data += 'Random abilities (slots 1-7)\n'
        for i in range(178, 402, 2):
            if i == 178:
                monster_data += 'Tidus   '
            elif i == 210:
                monster_data += 'Yuna    '
            elif i == 242:
                monster_data += 'Auron   '
            elif i == 274:
                monster_data += 'Kimahri '
            elif i == 306:
                monster_data += 'Wakka   '
            elif i == 338:
                monster_data += 'Lulu    '
            elif i == 370:
                monster_data += 'Rikku   '
            if prize_struct[i + 1] == 128:
                ability = ffx_info.abilities[prize_struct[i]]['name']
                monster_data += f'[{ability:>15}]'
            else:
                monster_data += '[---------------]'
            if i % 16 == 0:
                monster_data += '\n'
            if i % 32 == 0:
                monster_data += '        '
    else:
        monster_data += 'No equipment drops'
    monster_data += '\n'
    # print raw data
    for byte, index in zip(prize_struct, range(480)):
        # every 16 bytes make a new line
        if index % 16 == 0:
            monster_data += '\n'
            monster_data += ' '.join(
                [f'[{hex(index + i)[2:]:>3}]' for i in range(16)])
            monster_data += '\n'
        # print the bytes' value
        # monster_data += f' {hex(byte)[2:]:>3}  '
        monster_data += f' {byte:>3}  '
        # sections
        if index == 0x80 - 1:
            monster_data += '\nPrize struct'
        elif index == 0xB0 - 1:
            monster_data += '\n             start of equipment'
        elif index == 0x190 - 1:
            monster_data += '\n             end of equipment'

    monster_data_text.config(state='normal')
    monster_data_text.delete(1.0, 'end')
    monster_data_text.insert(1.0, monster_data)
    monster_data_text.config(state='disabled')


ffx_info = FFXInfo()

monster_names = sorted(list(ffx_info.monsters_data.keys()))

# GUI
root = tk.Tk()


def on_ui_close():
    global root
    root.quit()
    quit()


root.protocol('WM_DELETE_WINDOW', on_ui_close)
root.title('ffx_monster_data_viewer')
root.geometry('1280x800')

main_font = font.Font(family='Courier New', size=9)

monster_data_text_scrollbar = tk.Scrollbar(root)
monster_data_text_scrollbar.pack(fill='y', side='right')

monster_data_text = tk.Text(root, font=main_font, width=55)
monster_data_text.pack(expand=True, fill='both', side='right')
monster_data_text.config(yscrollcommand=monster_data_text_scrollbar.set)

monster_data_text_scrollbar.config(command=monster_data_text.yview)

monsters_listbox_var = tk.StringVar(value=monster_names)
monsters_listbox = tk.Listbox(
    root,
    width=30,
    height=800,
    listvariable=monsters_listbox_var)

monsters_listbox.bind(
    "<<ListboxSelect>>",
    lambda _: print_monster_data(
        monsters_listbox.curselection(),
        monster_data_text))

monsters_listbox.pack(fill='y', side='left')

root.mainloop()
