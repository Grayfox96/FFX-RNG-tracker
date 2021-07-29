import ffx_rng_tracker
import tkinter as tk
from tkinter import font
from typing import Union


class BetterSpinbox(tk.Spinbox):
    '''Upgraded spinbox with a set() method and readonly by default.'''

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config(state='readonly')

    def set(self, text: Union[str, int]) -> None:
        '''Set the spinbox content.'''
        self.config(state='normal')
        self.delete(0, 'end')
        self.insert(0, text)
        self.config(state='readonly')


def on_ui_close():
    '''Close the ui and quit the program.'''
    root.quit()
    quit()


def on_mousewheel(event):
    '''If the widget under the cursor is a spinbox,
    it increments/decrements it on wheelup/wheeldown.
    '''
    # get widget under cursor
    x, y = root.winfo_pointerxy()
    widget = root.winfo_containing(x, y)
    # increment or decrement based on scroll direction
    if isinstance(widget, BetterSpinbox) or isinstance(widget, tk.Spinbox):
        if event.delta == 120:
            widget.invoke('buttonup')
        elif event.delta == -120:
            widget.invoke('buttondown')


def character_damage_tracker(parent, index: int) -> None:
    '''Setup spinboxes and a text to track character rng.'''
    def get_character_rng_position():
        position = int(tracker['attacks'].get()) * 2
        position += int(tracker['healing_items'].get())
        position += int(tracker['escapes'].get())
        position += int(tracker['manual_rng'].get())

        if index == 0:
            position += int(tracker['haste'].get())
            position += int(tracker['armor_break'].get()) * 2
            position += int(tracker['spiral_cut'].get()) * 4
        elif index == 1:
            position += int(tracker['cure'].get())
        elif index == 2:
            position += int(tracker['power_break'].get()) * 2
            position += int(tracker['overdrive'].get()) * 4
        elif index == 3:
            position += int(tracker['lancet'].get()) * 2
            position += int(tracker['overdrive'].get()) * 2
        elif index == 4:
            position += int(tracker['dark_attack'].get()) * 2
            position += int(tracker['elemental_reels'].get()) * 2
        elif index == 5:
            position += int(tracker['magic'].get())
            position += int(tracker['elemental_fury'].get()) * 16
        elif index == 6:
            position += int(tracker['grenade'].get()) * 2
            position += int(tracker['tier_2_grenade'].get())
            position += int(tracker['aoe_mixes'].get()) * 2
            position += int(tracker['9_hit_mixes'].get()) * 9
        elif index == 7:
            position += int(tracker['special_attack'].get()) * 2
            position += int(tracker['magic'].get())
            position += int(tracker['overdrives'].get())
        return position

    def spinbox_command():
        '''Update the text based on the spinboxes values.'''
        position = int(encounters.get()) - int(preemptives.get())
        if position < 0:
            position = 0
        if index > 6:
            position = position * 11

        position += get_character_rng_position()

        data = ''
        for i in range(0, 40):

            if i % 2 == 0:
                data += f'[{(i // 2) + 1:2}]'
            else:
                data += '    '

            rng_damage = rng_tracker.rng_arrays[20 + index][position + i]
            damage_roll = rng_damage & 31

            rng_crit = rng_tracker.rng_arrays[20 + index][position + i + 1]
            crit_roll = rng_crit % 101
            luck = int(tracker['luck'].get())

            target_luck = int(monster_luck.get())
            equipment_crit = int(tracker['equipment_crit'].get())

            crit_chance = luck - target_luck + equipment_crit
            if crit_roll < crit_chance:
                crit = 'C'
            else:
                crit = ' '

            od_crit_chance = luck - target_luck
            if crit_roll < od_crit_chance:
                od_crit = 'ODC'
            else:
                od_crit = '   '

            rng_escape = rng_tracker.rng_arrays[20 + index][position + i]
            escape_roll = rng_escape & 255
            if escape_roll < 191:
                escape = 'E'
            else:
                escape = ' '

            data += f' {damage_roll:>2}/31 [{crit}][{od_crit}][{escape}]\n'

        tracker['text'].config(state='normal')
        tracker['text'].delete(1.0, 'end')
        tracker['text'].insert(1.0, data)
        tracker['text'].config(state='disabled')

    def hide_command():
        tracker['frame'].grid_remove()
        tracker['visible'] = False

    def make_spinbox(row, label):
        tk.Label(tracker['frame'],
                 text=label).grid(row=row, column=0, sticky='e')
        spinbox = BetterSpinbox(tracker['frame'],
                                from_=0,
                                to=1000,
                                command=tracker['spinbox_command'])
        spinbox.grid(row=row, column=1, sticky='nsew')
        return spinbox

    tracker = {
        'visible': True,
        'spinbox_command': spinbox_command,
    }

    tracker['frame'] = tk.Frame(parent)
    tracker['frame'].grid(row=0, column=index, sticky='nsew')

    if index < 7:
        character = rng_tracker.CHARACTERS[index]
    elif index == 7:
        character = 'Aeons'
    tk.Label(tracker['frame'], text=character).grid(row=0,
                                                    column=0,
                                                    sticky='nsew')

    tracker['hide_button'] = tk.Button(tracker['frame'],
                                       text='Hide',
                                       command=hide_command)
    tracker['hide_button'].grid(row=0, column=1)

    tracker['attacks'] = make_spinbox(1, 'Attacks')
    if index in (0, 2):
        tracker['attacks'].set(3)

    if index == 0:
        tracker['haste'] = make_spinbox(2, 'Haste')
        tracker['armor_break'] = make_spinbox(3, 'Armor Break')
        tracker['spiral_cut'] = make_spinbox(4, 'Spiral Cut')
        tk.Label(tracker['frame'], text='').grid(row=5, column=0)
    elif index == 1:
        tracker['cure'] = make_spinbox(2, 'Cure')
        tk.Label(tracker['frame'], text='').grid(row=3, column=0)
        tk.Label(tracker['frame'], text='').grid(row=4, column=0)
        tk.Label(tracker['frame'], text='').grid(row=5, column=0)
    elif index == 2:
        tracker['power_break'] = make_spinbox(2, 'Power Break')
        tracker['overdrive'] = make_spinbox(3, 'Overdrive')
        tk.Label(tracker['frame'], text='').grid(row=4, column=0)
        tk.Label(tracker['frame'], text='').grid(row=5, column=0)
    elif index == 3:
        tracker['lancet'] = make_spinbox(2, 'Lancet')
        tracker['overdrive'] = make_spinbox(3, 'Overdrive')
        tk.Label(tracker['frame'], text='').grid(row=4, column=0)
        tk.Label(tracker['frame'], text='').grid(row=5, column=0)
    elif index == 4:
        tracker['dark_attack'] = make_spinbox(2, 'Dark Attack')
        tracker['elemental_reels'] = make_spinbox(3, 'Elemental Reels')
        tk.Label(tracker['frame'], text='').grid(row=4, column=0)
        tk.Label(tracker['frame'], text='').grid(row=5, column=0)
    elif index == 5:
        tracker['magic'] = make_spinbox(2, 'ST Magic')
        tracker['elemental_fury'] = make_spinbox(3, 'Elemental Fury')
        tk.Label(tracker['frame'], text='').grid(row=4, column=0)
        tk.Label(tracker['frame'], text='').grid(row=5, column=0)
    elif index == 6:
        tracker['grenade'] = make_spinbox(2, 'Grenade')
        tracker['tier_2_grenade'] = make_spinbox(3, 'Tier 2 Grenade')
        tracker['aoe_mixes'] = make_spinbox(4, 'AoE Damage Mixes')
        tracker['9_hit_mixes'] = make_spinbox(5, '9-Hit Mixes')
    elif index == 7:
        tracker['special_attack'] = make_spinbox(2, 'Special Attack')
        tracker['magic'] = make_spinbox(3, 'ST Magic')
        tracker['overdrives'] = make_spinbox(4, 'Overdrive')
        tk.Label(tracker['frame'], text='').grid(row=5, column=0)

    tracker['healing_items'] = make_spinbox(17, 'Healing Items')
    tracker['escapes'] = make_spinbox(18, 'Escapes')
    tracker['manual_rng'] = make_spinbox(19, 'Manual RNG')

    tracker['text'] = tk.Text(tracker['frame'],
                              font=main_font,
                              state='disabled')
    tracker['text'].grid(row=20, column=0, columnspan=2, sticky='nsew')

    tracker['luck'] = make_spinbox(21, 'Luck')
    base_luck = (18, 17, 17, 18, 19, 17, 18, 17)
    tracker['luck'].set(base_luck[index])

    tracker['equipment_crit'] = make_spinbox(22, 'Equipment Crit')
    default_equipment_crit = (6, 6, 6, 3, 3, 6, 6, 6)
    tracker['equipment_crit'].set(default_equipment_crit[index])

    tracker['frame'].columnconfigure(1, weight=1)
    tracker['frame'].rowconfigure(20, weight=1)

    return tracker


def update_tracker():
    '''Update every character's text.'''
    for character, tracker in trackers.items():
        if tracker['visible']:
            tracker['spinbox_command']()


def get_monster_luck(*args):
    '''Get a monster's Luck stat from it's prize struct.'''
    name = monster.get()
    try:
        prize_struct = rng_tracker.monsters_data[name]
    except KeyError:
        return
    luck = prize_struct[37]
    monster_luck.set(luck)
    update_tracker()


damage_rolls_input = input('Damage rolls (Auron1 Tidus1 A2 T2 A3 T3): ')

# replace different symbols with spaces
for symbol in (',', '-', '/', '\\'):
    damage_rolls_input = damage_rolls_input.replace(symbol, ' ')

# fixes double spaces
damage_rolls_input = ' '.join(damage_rolls_input.split())

damage_rolls_input = tuple(
    [int(damage_roll) for damage_roll in damage_rolls_input.split(' ')])

rng_tracker = ffx_rng_tracker.FFXRNGTracker(damage_rolls_input)

# GUI
root = tk.Tk()

root.protocol('WM_DELETE_WINDOW', on_ui_close)
root.title('ffx_rng_damage_tracker')
root.geometry('1280x830')

main_font = font.Font(family='Courier New', size=9)

root.bind_all("<MouseWheel>", on_mousewheel)

for i in range(1, 9):
    root.columnconfigure(i, weight=1)

root.rowconfigure(1, weight=1)

tk.Label(root, text='Encounters:').grid(row=0, column=0, sticky='e')
encounters = BetterSpinbox(root, from_=0, to=1000)
encounters.grid(row=0, column=1, sticky='ew')
encounters.set(2)

tk.Label(root, text='Preemptives/ambushes:').grid(row=0, column=2, sticky='e')
preemptives = BetterSpinbox(root, from_=0, to=1000)
preemptives.grid(row=0, column=3, sticky='ew')

monster_label = tk.Label(root, text='Monster:')
monster_label.grid(row=0, column=4, sticky='e')

monster_names = sorted(list(rng_tracker.monsters_data.keys()))

monster = tk.Spinbox(root, values=monster_names)
monster.grid(row=0, column=5, sticky='ew')

monster_luck_label = tk.Label(root, text='Enemy Luck:')
monster_luck_label.grid(row=0, column=6, sticky='e')

monster_luck = BetterSpinbox(root, from_=0, to=255)
monster_luck.grid(row=0, column=7, sticky='ew')

frame = tk.Frame(root)
frame.grid(row=1, column=0, columnspan=8, sticky='nsew')

trackers = {
    'tidus': character_damage_tracker(frame, 0),
    'yuna': character_damage_tracker(frame, 1),
    'auron': character_damage_tracker(frame, 2),
    'kimahri': character_damage_tracker(frame, 3),
    'wakka': character_damage_tracker(frame, 4),
    'lulu': character_damage_tracker(frame, 5),
    'rikku': character_damage_tracker(frame, 6),
    'aeons': character_damage_tracker(frame, 7),
}

for i in range(8):
    frame.columnconfigure(i, weight=1)

frame.rowconfigure(0, weight=1)

encounters.config(command=update_tracker)
preemptives.config(command=update_tracker)
monster_luck.config(command=update_tracker)

monster.bind('<KeyRelease>', get_monster_luck)
monster.config(command=get_monster_luck)

monster.delete(0, 'end')
monster.insert(0, 'sinspawn_ammes')

get_monster_luck()

root.mainloop()
