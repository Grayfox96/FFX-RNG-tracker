import ffx_rng_tracker
import tkinter as tk
from tkinter import font

damage_rolls_input = input('Damage rolls (Auron1 Tidus1 A2 T2 A3 T3): ')

# replace different symbols with spaces
for symbol in (',', '-', '/', '\\'):
    damage_rolls_input = damage_rolls_input.replace(symbol, ' ')

# fixes double spaces
damage_rolls_input = ' '.join(damage_rolls_input.split())

damage_rolls_input = tuple(
    [int(damage_roll) for damage_roll in damage_rolls_input.split(' ')])

rng_tracker = ffx_rng_tracker.FFXRNGTracker(damage_rolls_input)

for equipment_number, equipment_type in enumerate(
        rng_tracker.get_equipment_types(50)):
    print(f'Equipment {equipment_number + 1:>2}: {equipment_type}')


def parse_notes(data_text):

    def highlight_pattern(
            text, pattern, tag, start='1.0', end='end', regexp=False):
        start = text.index(start)
        end = text.index(end)
        text.mark_set('matchStart', start)
        text.mark_set('matchEnd', start)
        text.mark_set('searchLimit', end)
        count = tk.IntVar()
        while True:
            index = text.search(
                pattern,
                'matchEnd',
                'searchLimit',
                count=count,
                regexp=regexp)
            if index == '':
                break
            if count.get() == 0:
                break  # degenerate pattern which matches zero-length strings
            text.mark_set('matchStart', index)
            text.mark_set('matchEnd', f'{index}+{count.get()}c')
            text.tag_add(tag, 'matchStart', 'matchEnd')

    def get_equipment_counter():
        i = 0
        while True:
            i += 1
            yield i

    def event_steal(*params):

        if len(params) == 1:
            monster_name, successful_steals = params[0], 0
        elif len(params) >= 2:
            (monster_name, successful_steals) = params[:2]
        else:
            rng_tracker.add_comment_event(
                'Usage: steal [enemy_name] (successful steals)')
            return

        try:
            successful_steals = int(successful_steals)
        except ValueError:
            rng_tracker.add_comment_event(
                'Usage: steal [enemy_name] (successful steals)')
            return

        try:
            rng_tracker.add_steal_event(monster_name, successful_steals)
        except KeyError:
            rng_tracker.add_comment_event(f'No monster named {monster_name}')

    def event_kill(*params):

        if len(params) < 2:
            rng_tracker.add_comment_event('Usage: kill [enemy_name] [killer]')
            return
        elif len(params) >= 2:
            (monster_name, killer) = params[:2]

        try:
            rng_tracker.add_kill_event(monster_name, killer)
        except KeyError:
            rng_tracker.add_comment_event(f'No monster named {monster_name}')

    def event_death(*params):

        if len(params) == 0:
            character = '???'
        else:
            character = params[0]

        rng_tracker.add_death_event(character)

    def event_roll(*params):

        if len(params) == 1:
            rng_index, number_of_times = params[0][3:], 1
        elif len(params) >= 2:
            rng_index, number_of_times = params[0][3:], params[1]
        else:
            rng_tracker.add_comment_event(
                'Usage: waste/advance/roll [rng#] [amount]')
            return

        if len(rng_index) == 0:
            rng_tracker.add_comment_event(
                'Usage: waste/advance/roll [rng#] [amount]')
            return

        try:
            rng_index, number_of_times = int(rng_index), int(number_of_times)
        except ValueError:
            rng_tracker.add_comment_event(
                'Usage: waste/advance/roll [rng#] [amount]')
            return

        if rng_index in rng_tracker.rng_current_positions:
            rng_tracker.add_advance_rng_event(rng_index, number_of_times)
        else:
            rng_tracker.add_comment_event(f'Can\'t advance rng{rng_index}')

    # aliases
    event_advance = event_roll
    event_waste = event_roll

    def event_party(*params):

        if len(params) == 0:
            rng_tracker.add_comment_event(
                'Usage: party [party members initials]')
            return

        new_party_formation = ''.join(params)

        if any(character in new_party_formation for character in (
                't', 'y', 'a', 'k', 'w', 'l', 'r')) is False:
            rng_tracker.add_comment_event(
                'Usage: party [party members initials]')
            return

        rng_tracker.add_change_party_event(new_party_formation)

    rng_tracker.reset_variables()

    notes_lines_array = notes_text.get('1.0', 'end').split('\n')

    # parse through the input text
    for line in notes_lines_array:

        # if the line is empty add an empty comment
        if line == '':
            rng_tracker.add_comment_event('')

        # if line starts with # add it as a comment
        elif line[0] == '#':
            rng_tracker.add_comment_event(line)

        # if the line is not a comment use it to call a function
        else:

            # fixes double spaces
            line = ' '.join(line.split())

            line = line.lower()

            event, *params = [split for split in line.split(' ')]

            # call the appropriate event function
            try:
                locals()[f'event_{event}'](*params)

            # if event doesnt exists add a comment with an error message
            except KeyError as error:
                rng_tracker.add_comment_event(f'No event called {event}')

    equipment_counter = get_equipment_counter()

    data = ''

    for event in rng_tracker.events_sequence:

        if event['name'] == 'steal':

            # replace underscores with spaces and capitalize words
            words = event['monster_name'].split('_')
            monster_name = ' '.join([word[0].upper() + word[1:].lower()
                                     for word in words])

            data += f'Steal from {monster_name}: '

            if event['item']:

                rarity = '' if event['item']['rarity'] == 'common' else ' (rare)'

                data += (f'{event["item"]["name"]} '
                         f'x{event["item"]["quantity"]}{rarity}')

            else:

                data += 'Failed'

        elif event['name'] == 'kill':

            # replace underscores with spaces and capitalize words
            words = event['monster_name'].split('_')
            monster_name = ' '.join([word[0].upper() + word[1:]
                                     for word in words])

            data += f'{monster_name} drops: '

            if event['item1']:

                if event['item1']['rarity'] == 'common':
                    rarity = ''
                else:
                    rarity = ' (rare)'

                data += (f'{event["item1"]["name"]} '
                         f'x{event["item1"]["quantity"]}{rarity}')

            if event['item2']:

                if event['item2']['rarity'] == 'common':
                    rarity = ''
                else:
                    rarity = ' (rare)'

                data += (f', {event["item2"]["name"]} '
                         f'x{event["item2"]["quantity"]}{rarity}')

            if event['equipment']:

                equipment = event['equipment']

                if equipment['guaranteed']:
                    guaranteed_equipment = ' (guaranteed)'
                else:
                    guaranteed_equipment = ''

                data += (f', Equipment #{next(equipment_counter)}'
                         f'{guaranteed_equipment}: {equipment["name"]} '
                         f'({equipment["owner"]}) {equipment["abilities"]} '
                         f'[{equipment["sell_gil_value"]} gil]')

            # if all 3 are None
            if (event['item1'] is None
                and event['item2'] is None
                and event['equipment'] is None):
                data += 'No drops'

        elif event['name'] == 'death':
            data += f'Character death: {event["dead_character"]}'

        elif event['name'] == 'advance_rng':
            data += (f'Advanced rng{event["rng_index"]} '
                     f'{event["number_of_times"]} times')

        elif event['name'] == 'change_party':
            data += f'Party changed to: {", ".join(event["party"])}'

        elif event['name'] == 'comment':

            data += event['text']

            # if the text contains /// it hides the lines before it
            if '///' in event['text']:
                data = ''

        data += '\n'

    # remove the last newline
    data = data[:-2]

    saved_position = data_scrollbar.get()

    data_text.config(state='normal', yscrollcommand=None)
    data_text.delete(1.0, 'end')
    data_text.insert(1.0, data)

    highlight_pattern(data_text, 'Equipment', 'equipment')
    highlight_pattern(data_text, 'No Encounters', 'no_encounters')
    highlight_pattern(data_text, '^#(.+?)?$', 'comment', regexp=True)
    highlight_pattern(data_text, '^Advanced rng.+$', 'rng_rolls', regexp=True)

    # highlight error messages
    error_messages = (
        'Invalid',
        'No event called',
        'Usage:',
        'No monster named',
        'Can\'t advance',
    )

    for error_message in error_messages:
        highlight_pattern(
            data_text,
            f'^{error_message}.+$',
            'error',
            regexp=True)

    data_text.config(state='disabled', yscrollcommand=data_scrollbar.set)

    data_text.yview('moveto', saved_position[0])


# GUI
root = tk.Tk()


def on_ui_close():
    global root
    root.quit()
    quit()


root.protocol('WM_DELETE_WINDOW', on_ui_close)
root.title('ffx_rng_tracker')
root.geometry('1368x800')

# Texts

texts_font = font.Font(family='Courier New', size=9)

# notes
# width in characters
notes_width = 40

notes_canvas = tk.Canvas(root, width=notes_width)
notes_canvas.pack(fill='y', side='left')

notes_text = tk.Text(notes_canvas, font=texts_font, width=notes_width)
notes_text.pack(fill='y', side='left')

notes_text.bind('<KeyRelease>', lambda _: parse_notes(data_text))

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


def get_notes(default_notes_file):
    with open(ffx_rng_tracker.get_resource_path(default_notes_file)) as \
            notes_file:
        return notes_file.read()


try:
    default_notes = get_notes('ffxhd_rng_tracker_notes.txt')
except FileNotFoundError:
    default_notes = get_notes('files/ffxhd_rng_tracker_default_notes.txt')

notes_text.insert('end', default_notes)

parse_notes(data_text)

root.mainloop()
