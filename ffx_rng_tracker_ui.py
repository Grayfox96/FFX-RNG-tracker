from ffx_rng_tracker import *
import tkinter as tk
from tkinter import font, ttk, simpledialog
from itertools import count


class BetterText(tk.Text):
    '''Upgraded Text widget.'''

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

    def highlight_pattern(
            self, pattern: str, tag: str, start: str = '1.0',
            end: str = 'end', regexp: bool = False) -> None:
        start = self.index(start)
        end = self.index(end)
        self.mark_set('matchStart', start)
        self.mark_set('matchEnd', start)
        self.mark_set('searchLimit', end)
        count = tk.IntVar()
        while True:
            index = self.search(
                pattern, 'matchEnd', 'searchLimit', count=count, regexp=regexp)
            if index == '' or count.get() == 0:
                break
            self.mark_set('matchStart', index)
            self.mark_set('matchEnd', f'{index}+{count.get()}c')
            self.tag_add(tag, 'matchStart', 'matchEnd')


class BetterSpinbox(tk.Spinbox):
    '''Upgraded spinbox widget with a set() method
    and readonly by default.
    '''

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config(state='readonly')

    def set(self, text: Union[str, int]) -> None:
        '''Set the spinbox content.'''
        self.config(state='normal')
        self.delete(0, 'end')
        self.insert(0, text)
        self.config(state='readonly')


class FFXSeedInfoUI(tk.Frame):
    '''Widget that shows general information
    about the seed.
    '''

    def __init__(self, parent, rng_tracker, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.rng_tracker = rng_tracker
        self.main_font = font.Font(family='Courier New', size=9)
        self.text = self.make_equipmnent_types_widget()

    def make_equipmnent_types_widget(self):
        data = [
            f'Seed number: {self.rng_tracker.seed_number}',
            f'Damage rolls: {self.get_damage_rolls()}',
            self.get_status_misses(),
            self.get_equipment_types(50, 5),
        ]
        data = '\n\n'.join(data)
        widget = BetterText(self, font=self.main_font, wrap='none')
        widget.pack(expand=True, fill='both')
        widget.insert('end', data)
        widget.tag_configure('armor', foreground='#0000ff')
        widget.highlight_pattern('armor', 'armor')
        widget.config(state='disabled')
        return widget

    def get_equipment_types(self, amount, columns=2):
        equipment_types = self.rng_tracker.get_equipment_types(amount)
        spacer = f'{"".join(["-" for i in range(16 * columns + 1)])}\n'
        data = f'First {amount} equipment types\n{spacer}'
        for _ in range(columns):
            data += f'| [##] |   Type '
        data += f'|\n{spacer}'
        for i in range(amount // columns):
            for j in range(columns):
                j = j * (amount // columns)
                data += f'| [{i + j + 1:2}] | {equipment_types[i + j]:>6} '
            data += '|\n'
        data += spacer
        return data

    def get_damage_rolls(self):
        damage_rolls = (
            self.rng_tracker.damage_rolls['auron'][1],
            self.rng_tracker.damage_rolls['tidus'][1],
            self.rng_tracker.damage_rolls['auron'][2],
            self.rng_tracker.damage_rolls['tidus'][2],
            self.rng_tracker.damage_rolls['auron'][3],
            self.rng_tracker.damage_rolls['tidus'][3],
        )
        damage_rolls = ', '.join([str(i) for i in damage_rolls])
        return damage_rolls

    def get_status_misses(self):
        output = []
        if (self.rng_tracker.rng_arrays[54][0] % 101) == 100:
            output.append('Auron\'s Power Break Miss: Yes')
        else:
            output.append('Auron\'s Power Break Miss: No')

        if (self.rng_tracker.rng_arrays[56][0] % 101) == 100:
            output.append('Wakka\'s Dark Attack Miss: Yes')
        else:
            output.append('Wakka\'s Dark Attack Miss: No')

        return '\n'.join(output)


class FFXEncountersRNGTrackerUI(tk.Frame):
    '''Widget used to track encounters RNG.'''

    def __init__(self, parent, rng_tracker, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.rng_tracker = rng_tracker
        self.formations = rng_tracker.formations
        self.main_font = font.Font(family='Courier New', size=9)
        self.data = self.make_data_widget()
        self.sliders_settings = self.get_sliders_settings(
            'files/ffx_rng_encounters_settings.csv')
        self.encounters = self.make_encounters_widget()
        self.print_data()

    def get_sliders_settings(self, settings_file):
        sliders_settings = {}
        with open(get_resource_path(settings_file)) as settings_file_object:
            settings_file_reader = csv.reader(
                settings_file_object, delimiter=',')

            # skips first line
            next(settings_file_reader)

            for line in settings_file_reader:
                sliders_settings[line[0]] = {
                    'min': line[1],
                    'default': line[2],
                    'max': line[3],
                }
        return sliders_settings

    def make_data_widget(self):
        '''Adds the data widget to the UI and returns a dictionary
        containing the widget's components.
        '''
        widget = {}
        widget['frame'] = tk.Frame(self)
        widget['frame'].pack(expand=True, fill='both', side='right')
        widget['text'] = BetterText(
            widget['frame'], font=self.main_font, width=57, state='disabled')
        widget['text'].tag_configure('ambush', foreground='#ff0000')
        widget['text'].tag_configure('preemptive', foreground='#00ff00')
        widget['text'].tag_configure(
            'enemy', background='#ffff00', selectforeground='#000000')
        widget['text'].pack(expand=True, fill='both', side='left')
        widget['scrollbar'] = tk.Scrollbar(widget['frame'])
        widget['scrollbar'].pack(fill='y', side='right')
        widget['scrollbar'].config(command=widget['text'].yview)
        widget['text'].configure(yscrollcommand=widget['scrollbar'].set)
        return widget

    def make_encounters_widget(self):
        '''Adds the encounters tracking widget to the UI and returns
        a dictionary containing the widget's components.
        '''
        def make_sliders(parent):
            widget = {}
            widget['variable'] = tk.StringVar()
            row_counter = count(1)
            radiobutton = tk.Radiobutton(
                parent, text='Start', variable=widget['variable'],
                value='Start', command=self.print_data)
            radiobutton.grid(row=0, column=1, columnspan=2, sticky='sw')
            for zone, settings in self.sliders_settings.items():
                row = next(row_counter)
                min = settings['min']
                default = settings['default']
                max = settings['max']
                widget[zone] = {}
                widget[zone] = tk.Scale(
                    parent, orient='horizontal', label=None, from_=min, to=max,
                    command=lambda _: self.print_data())
                widget[zone].set(default)
                widget[zone].grid(row=row, column=0)
                radiobutton = tk.Radiobutton(
                    parent, text=zone, variable=widget['variable'], value=zone,
                    command=self.print_data)
                radiobutton.grid(row=row, column=1, sticky='sw')
            return widget

        widget = {}
        widget['outer_frame'] = tk.Frame(self)
        widget['outer_frame'].pack(fill='y', side='left')
        widget['canvas'] = tk.Canvas(widget['outer_frame'], width=280)
        widget['canvas'].pack(side='left', fill='both', expand=True)
        widget['scrollbar'] = tk.Scrollbar(
            widget['outer_frame'], orient='vertical',
            command=widget['canvas'].yview)
        widget['scrollbar'].pack(side='right', fill='y')
        widget['canvas'].configure(yscrollcommand=widget['scrollbar'].set)
        widget['inner_frame'] = tk.Frame(widget['canvas'])
        widget['inner_frame'].bind(
            '<Configure>', lambda _: widget['canvas'].configure(
                scrollregion=widget['canvas'].bbox('all')))
        widget['canvas'].create_window(
            (0, 0), window=widget['inner_frame'], anchor='nw')
        # when the mouse enters the canvas it binds the mousewheel to scroll
        widget['canvas'].bind(
            '<Enter>',
            lambda _: widget['canvas'].bind_all(
                '<MouseWheel>',
                lambda e: widget['canvas'].yview_scroll(
                    int(-1 * (e.delta / 120)), 'units')))
        # when the mouse leaves the canvas it unbinds the mousewheel
        widget['canvas'].bind(
            '<Leave>', lambda _: widget['canvas'].unbind_all('<MouseWheel>'))
        widget['sliders'] = make_sliders(widget['inner_frame'])
        return widget

    def print_data(self):
        '''Sets the content of the data widget to a string
        containing encounters information.
        '''
        def get_condition(initiative=False):
            condition_rng = self.rng_tracker.advance_rng(1) & 255
            condition = 2
            if initiative:
                condition_rng += -32 - 1
            if condition_rng < (255 - 32):
                condition = 1 if condition_rng < 32 else 0
            if condition == 0:
                output = ''
            elif condition == 1:
                output = 'Preemptive'
            elif condition == 2:
                output = 'Ambush'
            return output

        def get_formation(zone, rng_value=None):
            if rng_value is None:
                rng_value = self.rng_tracker.advance_rng(1)
            formation_number = rng_value % len(self.formations[zone])
            return self.formations[zone][formation_number]

        def add_random_encounters(zone, initiative=False):
            if self.encounters['sliders']['variable'].get() == zone:
                data.clear()
            encounters = self.encounters['sliders'][zone].get()
            for number in range(encounters):
                formation = get_formation(zone)
                condition = get_condition(initiative)
                data.append(f'{next(total_counter):3}: {zone} [{number + 1}]')
                data.append(
                    f'   `-{next(random_counter):3}: {formation:{padding}}'
                    f'{condition}')

        def add_forced_encounters(encounter_names, initiative=False):
            for encounter_name in encounter_names:
                condition = get_condition(initiative)
                data.append(
                    f'{next(total_counter):3}: {encounter_name:{padding + 5}}'
                    f'{condition}')

        def add_optional_forced_encounters(encounter_name, initiative=False):
            if self.encounters['sliders']['variable'].get() == encounter_name:
                data.clear()
            encounters = self.encounters['sliders'][encounter_name].get()
            for number in range(encounters):
                condition = get_condition(initiative)
                data.append(
                    f'{next(total_counter):3}: {encounter_name:{padding + 5}}'
                    f'{condition}')

        def add_simulated_encounters(encounter_name):
            if self.encounters['sliders']['variable'].get() == encounter_name:
                data.clear()
            encounters = self.encounters['sliders'][encounter_name].get()
            for number in range(encounters):
                self.rng_tracker.advance_rng(1)
                data.append(f'   : {encounter_name}')

        def add_cave_encounters(initiative=False):
            '''Prints 2 encounters from the two different zones
            of the cave at the same time.
            '''
            if self.encounters['sliders']['variable'].get() == 'Cave':
                data.clear()
            encounters = self.encounters['sliders']['Cave'].get()
            for number in range(encounters):
                rng_value = self.rng_tracker.advance_rng(1)
                formation_white = get_formation('Cave (White Zone)', rng_value)
                formation_green = get_formation('Cave (Green Zone)', rng_value)
                formation = formation_white + '/' + formation_green
                condition = get_condition(initiative)
                data.append(f'{next(total_counter):3}: Cave [{number + 1}]')
                data.append(
                    f'   `-{next(random_counter):3}: {formation:{padding}}'
                    f'{condition}')

        self.rng_tracker.rng_current_positions[1] = 0
        data = []
        total_counter = count(1)
        random_counter = count(1)
        padding = 37

        add_forced_encounters(
            ('Sinscales', 'Ammes', 'Tanker', 'Sahagins', 'Geosgaeno', 'Klikk 1',
             'Klikk 2'))
        add_random_encounters('Underwater Ruins')
        add_forced_encounters(('Piranhas', 'Tros'))
        add_random_encounters('Besaid Lagoon')
        add_forced_encounters(
            ('Dingo/Condor', 'Water Flan', 'Kimahri', 'Garuda 1', 'Garuda 2',
             'Condor/Dingo/Water Flan'))
        add_random_encounters('Besaid Road')
        add_forced_encounters(('Sin Fin', 'Echuilles', 'Lancet tutorial'))
        add_optional_forced_encounters('Lord Ochu (Way In)')
        add_random_encounters('Kilika Woods (Way In)')
        add_forced_encounters(('Geneaux',))
        add_optional_forced_encounters('Lord Ochu (Way Out)')
        add_random_encounters('Kilika Woods (Way Out)')
        add_forced_encounters(
            ('Machina 1', 'Machina 2', 'Machina 3', 'Oblitzerator',
             'Sahagin Chiefs', 'Vouivre', 'Garuda', 'Pierce tutorial'))
        add_random_encounters('Miihen Screen 1')
        add_random_encounters('Miihen Screen 2/3')
        add_simulated_encounters('Simulation (Miihen)')
        add_forced_encounters(('Chocobo Eater',))
        add_random_encounters('Old Road')
        add_simulated_encounters('Simulation (Old Road)')
        add_random_encounters('Clasko Skip Screen')
        add_random_encounters('MRR - Valley')
        add_random_encounters('MRR - Precipice')
        add_forced_encounters(('Sinspawn Gui 1', 'Sinspawn Gui 2'))
        add_random_encounters('Djose Highroad (Front Half)', initiative=True)
        add_random_encounters('Djose Highroad (Back Half)', initiative=True)
        add_random_encounters('Moonflow (South)', initiative=True)
        add_forced_encounters(('Extractor', 'Rikku tutorial'))
        add_random_encounters('Moonflow (North)', initiative=True)
        add_random_encounters('Thunder Plains (South)', initiative=True)
        add_random_encounters('Thunder Plains (North)', initiative=True)
        add_random_encounters('Macalania Woods')
        add_forced_encounters(('Spherimorph',))
        add_random_encounters('Lake Macalania')
        add_forced_encounters(('Crawler', 'Seymour'))
        add_optional_forced_encounters('Guado Encounter')
        add_random_encounters('Crevasse')
        add_forced_encounters(('Wendigo', 'Zu'))
        add_random_encounters('Bikanel (Pre Machina)', initiative=True)
        add_forced_encounters(('Machina Steal tutorial',))
        add_random_encounters('Bikanel (Post Machina)', initiative=True)
        add_random_encounters('Bikanel (Central)', initiative=True)
        add_random_encounters('Bikanel (Ruins)', initiative=True)
        add_random_encounters('Bikanel (Pre Sandragora)', initiative=True)
        add_forced_encounters(('Sandragora 1',), initiative=True)
        add_optional_forced_encounters('Sandragora 1 refight', initiative=True)
        add_random_encounters('Bikanel (Post Sandragora)', initiative=True)
        add_forced_encounters(
            ('Sandragora 2', 'Guado + 3 Bombs', 'Guado + 2 Dual Horn 1',
             'Guado + 2 Chimera'), initiative=True)
        add_random_encounters('Airship')
        add_forced_encounters(
            ('Evrae', 'Bevelle Guards 1', 'Bevelle Guards 2',
             'Bevelle Guards 3', 'Bevelle Guards 4', 'Bevelle Guards 5'))
        add_random_encounters('Via Purifico', initiative=True)
        add_forced_encounters(
            ('Isaaru Grothia', 'Isaaru Pterya', 'Isaaru Spathi'))
        add_random_encounters('Via Purifico Underwater')
        add_forced_encounters(('Evrae Altana',))
        add_random_encounters('Highbridge', initiative=True)
        add_forced_encounters(('Seymour Natus',))
        add_simulated_encounters('Simulation (Calm Lands)')
        add_random_encounters('Calm Lands', initiative=True)
        add_forced_encounters(('Defender X',), initiative=True)
        add_optional_forced_encounters('Biran & Yenke')
        add_cave_encounters(initiative=True)

        data = '\n'.join(data)

        saved_position = self.data['scrollbar'].get()

        self.data['text'].configure(state='normal', yscrollcommand=None)
        self.data['text'].delete(1.0, 'end')
        self.data['text'].insert(1.0, data)

        self.data['text'].highlight_pattern('Preemptive', 'preemptive')
        self.data['text'].highlight_pattern('Ambush', 'ambush')

        for enemy in ('Bomb', 'Basilisk', 'Funguar', 'Iron Giant', 'Ghost'):
            self.data['text'].highlight_pattern(enemy, 'enemy')

        self.data['text'].configure(
            state='disabled', yscrollcommand=self.data['scrollbar'].set)

        self.data['text'].yview('moveto', saved_position[0])


class FFXDropsRNGTrackerUI(tk.Frame):
    '''Widget used to track enemy drops RNG.'''

    def __init__(self, parent, rng_tracker, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.rng_tracker = rng_tracker
        self.main_font = font.Font(family='Courier New', size=9)
        self.notes = self.make_notes_widget()
        self.data = self.make_data_widget()
        self.print_events()

    def get_notes(self):
        '''Get notes from a file, either custom or default.'''
        try:
            notes_file = open(get_resource_path('ffxhd_rng_tracker_notes.txt'))
        except FileNotFoundError:
            notes_file = open(get_resource_path(
                'files/ffxhd_rng_tracker_default_notes.txt'))
        notes = notes_file.read()
        notes_file.close()
        return notes

    def make_notes_widget(self):
        '''Add the notes widget to the UI and returns a dictionary
        containing the widget's components.
        '''
        widget = {}
        widget['frame'] = tk.Frame(self, width=40)
        widget['frame'].pack(fill='y', side='left')
        widget['text'] = tk.Text(
            widget['frame'], font=self.main_font, width=40)
        widget['text'].pack(fill='y', side='left')
        widget['text'].bind(
            '<KeyRelease>', lambda _: self.print_events())
        widget['text'].insert('end', self.get_notes())
        widget['scrollbar'] = tk.Scrollbar(
            widget['frame'], command=widget['text'].yview)
        widget['scrollbar'].pack(fill='y', side='right')
        widget['text'].config(yscrollcommand=widget['scrollbar'].set)
        return widget

    def make_data_widget(self):
        '''Add the data widget to the UI and returns a dictionary
        containing the widget's components.
        '''
        widget = {}
        widget['frame'] = tk.Frame(self)
        widget['frame'].pack(expand=True, fill='both', side='right')
        widget['text'] = BetterText(
            widget['frame'], font=self.main_font, state='disabled', wrap='word')
        widget['text'].pack(expand=True, fill='both', side='left')
        widget['text'].tag_configure('equipment', foreground='#0000ff')
        widget['text'].tag_configure('no_encounters', foreground='#00ff00')
        widget['text'].tag_configure('comment', foreground='#888888')
        widget['text'].tag_configure('rng_rolls', foreground='#ff0000')
        widget['text'].tag_configure('error', background='#ff0000')
        widget['text'].tag_configure('wrap_margin', lmargin2='1c')
        widget['scrollbar'] = tk.Scrollbar(widget['frame'])
        widget['scrollbar'].pack(fill='y', side='right')
        widget['scrollbar'].config(command=widget['text'].yview)
        widget['text'].configure(yscrollcommand=widget['scrollbar'].set)
        return widget

    def parse_notes(self):
        '''Parse through the event sequence and return a string
        containing all the relevant information.
        '''
        def event_steal(*params):
            if len(params) == 1:
                monster_name, successful_steals = params[0], 0
            elif len(params) >= 2:
                (monster_name, successful_steals) = params[:2]
            else:
                self.rng_tracker.add_comment_event(
                    'Usage: steal [enemy_name] (successful steals)')
                return
            try:
                successful_steals = int(successful_steals)
            except ValueError:
                self.rng_tracker.add_comment_event(
                    'Usage: steal [enemy_name] (successful steals)')
                return
            try:
                self.rng_tracker.add_steal_event(
                    monster_name, successful_steals)
            except KeyError:
                self.rng_tracker.add_comment_event(
                    f'No monster named {monster_name}')

        def event_kill(*params):
            if len(params) < 2:
                self.rng_tracker.add_comment_event(
                    'Usage: kill [enemy_name] [killer]')
                return
            elif len(params) >= 2:
                (monster_name, killer) = params[:2]
            try:
                self.rng_tracker.add_kill_event(monster_name, killer)
            except KeyError:
                self.rng_tracker.add_comment_event(
                    f'No monster named {monster_name}')

        def event_death(*params):
            if len(params) == 0:
                character = '???'
            else:
                character = params[0]
            self.rng_tracker.add_death_event(character)

        def event_roll(*params):
            if len(params) == 1:
                rng_index, times = params[0][3:], 1
            elif len(params) >= 2:
                rng_index, times = params[0][3:], params[1]
            else:
                self.rng_tracker.add_comment_event(
                    'Usage: waste/advance/roll [rng#] [amount]')
                return
            if len(rng_index) == 0:
                self.rng_tracker.add_comment_event(
                    'Usage: waste/advance/roll [rng#] [amount]')
                return
            try:
                rng_index, times = int(rng_index), int(times)
            except ValueError:
                self.rng_tracker.add_comment_event(
                    'Usage: waste/advance/roll [rng#] [amount]')
                return

            self.rng_tracker.add_advance_rng_event(rng_index, times)

        # aliases
        event_advance = event_roll
        event_waste = event_roll

        def event_party(*params):

            if len(params) == 0:
                self.rng_tracker.add_comment_event(
                    'Usage: party [party members initials]')
                return

            new_party_formation = ''.join(params)

            if any(character in new_party_formation for character in (
                    't', 'y', 'a', 'k', 'w', 'l', 'r')) is False:
                self.rng_tracker.add_comment_event(
                    'Usage: party [party members initials]')
                return

            self.rng_tracker.add_change_party_event(new_party_formation)

        self.rng_tracker.reset_variables()

        notes_lines = self.notes['text'].get('1.0', 'end').split('\n')

        # parse through the input text
        for line in notes_lines:
            # if the line is empty or starts with # add it as a comment
            if line == '' or line[0] == '#':
                self.rng_tracker.add_comment_event(line)
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
                    self.rng_tracker.add_comment_event(
                        f'No event called {event}')

    def print_events(self):
        '''Sets the content of the data widget to a string
        containing encounters information.
        '''
        equipment_counter = count(1)

        self.parse_notes()

        data = []

        for event in self.rng_tracker.events_sequence:
            if event['name'] == 'steal':
                # replace underscores with spaces and capitalize words
                words = event['monster_name'].split('_')
                monster_name = ' '.join([word[0].upper() + word[1:].lower()
                                         for word in words])
                result = f'Steal from {monster_name}: '

                # check if the steal succeeded
                if event['item']:
                    if event['item']['rarity'] == 'common':
                        rarity = ''
                    else:
                        rarity = ' (rare)'
                    result += (f'{event["item"]["name"]} '
                               f'x{event["item"]["quantity"]}{rarity}')
                else:
                    result += 'Failed'

                data.append(result)

            elif event['name'] == 'kill':
                # replace underscores with spaces and capitalize words
                words = event['monster_name'].split('_')
                monster_name = ' '.join([word[0].upper() + word[1:]
                                         for word in words])
                result = f'{monster_name} drops: '

                # check for drops
                if event['item1']:
                    if event['item1']['rarity'] == 'common':
                        rarity = ''
                    else:
                        rarity = ' (rare)'
                    result += (f'{event["item1"]["name"]} '
                               f'x{event["item1"]["quantity"]}{rarity}')

                if event['item2']:
                    if event['item2']['rarity'] == 'common':
                        rarity = ''
                    else:
                        rarity = ' (rare)'
                    result += (f', {event["item2"]["name"]} '
                               f'x{event["item2"]["quantity"]}{rarity}')

                if event['equipment']:
                    equipment = event['equipment']
                    if equipment['guaranteed']:
                        guaranteed_equipment = ' (guaranteed)'
                    else:
                        guaranteed_equipment = ''
                    if equipment['killer_is_owner']:
                        for_killer = ' (for killer)'
                    else:
                        for_killer = ''
                    result += (f', Equipment #{next(equipment_counter)}'
                               f'{guaranteed_equipment}{for_killer}: '
                               f'{equipment["name"]} '
                               f'({equipment["owner"]}) '
                               f'[{", ".join(equipment["abilities"])}]'
                               f'[{equipment["sell_gil_value"]} gil]')
                # if all 3 are None
                if (event['item1'] is None
                        and event['item2'] is None
                        and event['equipment'] is None):
                    result += 'No drops'

                data.append(result)

            elif event['name'] == 'death':
                data.append(f'Character death: {event["dead_character"]}')

            elif event['name'] == 'advance_rng':
                data.append(f'Advanced rng{event["rng_index"]} '
                            f'{event["number_of_times"]} times')

            elif event['name'] == 'change_party':
                data.append(f'Party changed to: {", ".join(event["party"])}')

            elif event['name'] == 'comment':
                # if the text contains /// it hides the lines before it
                if '///' in event['text']:
                    data.clear()
                else:
                    data.append(event['text'])

        data = '\n'.join(data)
        # save the scrollbar position
        saved_position = self.data['scrollbar'].get()
        # update the text widget
        self.data['text'].config(state='normal', yscrollcommand=None)
        self.data['text'].delete(1.0, 'end')
        self.data['text'].insert(1.0, data)
        self.data['text'].highlight_pattern('Equipment', 'equipment')
        self.data['text'].highlight_pattern('No Encounters', 'no_encounters')
        self.data['text'].highlight_pattern(
            '^#(.+?)?$', 'comment', regexp=True)
        self.data['text'].highlight_pattern(
            '^Advanced rng.+$', 'rng_rolls', regexp=True)

        # highlight error messages
        error_messages = (
            'Invalid',
            'No event called',
            'Usage:',
            'No monster named',
        )
        for error_message in error_messages:
            self.data['text'].highlight_pattern(
                f'^{error_message}.+$', 'error', regexp=True)

        self.data['text'].highlight_pattern('^.+$', 'wrap_margin', regexp=True)

        self.data['text'].config(
            state='disabled', yscrollcommand=self.data['scrollbar'].set)

        self.data['text'].yview('moveto', saved_position[0])


class FFXStatusRNGTrackerUI(tk.Frame):
    '''Widget that shows status RNG rolls.'''

    def __init__(self, parent, rng_tracker, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.rng_tracker = rng_tracker
        self.main_font = font.Font(family='Courier New', size=9)
        self.text = self.get_status_chance_text(99)

    def get_status_chance_text(self, rolls: int) -> str:
        '''Returns a table-formatted string of the status
        chance rng rolls for party members and enemies.
        '''
        status_chance_rolls = self.rng_tracker.get_status_chance_rolls(rolls)
        spacer = f'{"".join(["-" for i in range(157)])}\n'
        data = ('If status chance is 50%, 0-49 means succeed and 50-100 means '
                'fail.\nAbilities and attacks with 100% status chance fail with'
                ' a roll of 100.\nRNG is advanced only when an attack or '
                'ability that can cause a status effect is used.\n')
        data += spacer
        data += ('| Roll [###]|      Tidus|       Yuna|      Auron|    Kimahri'
                 '|      Wakka|       Lulu|      Rikku|      Aeons|    Enemy 1'
                 '|    Enemy 2|    Enemy 3|    Enemy 4|\n')
        data += spacer
        for i in range(rolls):
            data += f'| Roll [{i + 1:>3}]'
            for j in range(52, 64):
                data += f'| {status_chance_rolls[j][i]:>10}'
            data += '|\n'
        data += spacer
        text = BetterText(self, font=self.main_font, wrap='none')
        text.insert(1.0, data)
        text.config(state='disabled')
        text.pack(expand=True, fill='both')
        text.tag_configure('miss', foreground='#ff0000')
        text.highlight_pattern('  100', 'miss')
        return text


class FFXMonsterDataViewerUI(tk.Frame):
    '''Widget used to display information
    from the mon_data game file.
    '''

    def __init__(self, parent, rng_tracker, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.ffx_info = rng_tracker
        self.abilities = rng_tracker.abilities
        self.items = rng_tracker.items
        self.text_characters = rng_tracker.text_characters
        self.monsters_data = rng_tracker.monsters_data
        self.main_font = font.Font(family='Courier New', size=9)
        self.monsters_names = sorted(list(self.monsters_data.keys()))
        self.monster_data_widget = self.make_monster_data_widget()

    def get_monster_data(self, prize_struct):
        '''Get a dictionary with monster information.'''
        def add_bytes(address: int, length: int) -> int:
            '''Adds the value of adjacent bytes in a prize struct.'''
            value = 0
            for i in range(length):
                value += prize_struct[address + i] * (256 ** i)
            return value

        def get_elements() -> dict[str, str]:
            elements = {
                'Fire': 0b00001,
                'Ice': 0b00010,
                'Thunder': 0b00100,
                'Water': 0b01000,
                'Holy': 0b10000,
            }
            affinities = {}
            for element, value in elements.items():
                if prize_struct[43] & value:
                    affinities[element] = 'Absorbs'
                elif prize_struct[45] & value:
                    affinities[element] = 'Immune'
                elif prize_struct[46] & value:
                    affinities[element] = 'Halves'
                elif prize_struct[47] & value:
                    affinities[element] = 'Weak'
                else:
                    affinities[element] = 'Neutral'
            return affinities

        def get_item(address, offset):
            if prize_struct[address + 1 + (offset * 2)] == 32:
                item = {
                    'Name': self.items[prize_struct[address + (offset * 2)]],
                    'Quantity': prize_struct[address + 8 + offset],
                }
            else:
                item = 'None'
            return item

        def get_abilities(address):
            abilities = {}
            for equipment_type, offset in {'Weapon': 0, 'Armor': 16}.items():
                abilities[equipment_type] = []
                for i in range(address + offset, address + 16 + offset, 2):
                    if prize_struct[i + 1] == 128:
                        abilities[equipment_type].append(
                            self.abilities[prize_struct[i]]['name'])
                    else:
                        abilities[equipment_type].append('None')
            return abilities

        monster_name = ''
        for i in range(408, 430):
            if prize_struct[i] == 0:
                break
            monster_name += self.text_characters[prize_struct[i]]

        data = {
            'Name': monster_name,
            'Elements': get_elements(),
            'Auto-statuses': [],
        }

        data['Stats'] = {
            'HP': add_bytes(20, 4),
            'MP': add_bytes(24, 4),
            'Overkill threshold': add_bytes(28, 4),
            'Strength': prize_struct[32],
            'Defense': prize_struct[33],
            'Magic': prize_struct[34],
            'Magic Defense': prize_struct[35],
            'Agility': prize_struct[36],
            'Luck': prize_struct[37],
            'Evasion': prize_struct[38],
            'Accuracy': prize_struct[39],
        }
        data['Spoils'] = {
            'Gil': add_bytes(128, 2),
            'Regular AP': add_bytes(130, 2),
            'Overkill AP': add_bytes(132, 2),
            '???': add_bytes(134, 2),
        }
        # items
        data['Spoils']['Item 1'] = {
            'Drop chance': prize_struct[136],
            'Normal': {
                'Common': get_item(140, 0),
                'Rare': get_item(140, 1),
            },
            'Overkill': {
                'Common': get_item(152, 0),
                'Rare': get_item(152, 1),
            },
        }
        data['Spoils']['Item 2'] = {
            'Drop chance': prize_struct[137],
            'Normal': {
                'Common': get_item(140, 2),
                'Rare': get_item(140, 3),
            },
            'Overkill': {
                'Common': get_item(152, 2),
                'Rare': get_item(152, 3),
            },
        }
        data['Spoils']['Steal'] = {
            'Base chance': prize_struct[138],
        }

        if prize_struct[165] == 32:
            data['Spoils']['Steal']['Common'] = {
                'name': self.items[prize_struct[164]],
                'quantity': prize_struct[168],
            }
        else:
            data['Spoils']['Steal']['Common'] = 'None'
        if prize_struct[167] == 32:
            data['Spoils']['Steal']['Rare'] = {
                'name': self.items[prize_struct[166]],
                'quantity': prize_struct[169],
            }
        else:
            data['Spoils']['Steal']['Rare'] = 'None'
        if prize_struct[171] == 32:
            data['Spoils']['Bribe'] = {
                'name': self.items[prize_struct[170]],
                'quantity': prize_struct[172],
            }
        else:
            data['Spoils']['Bribe'] = 'None'

        data['Status resistances'] = {
            'Death': prize_struct[47],
            'Zombie': prize_struct[48],
            'Petrify': prize_struct[49],
            'Poison': prize_struct[50],
            'Power Break': prize_struct[51],
            'Magic Break': prize_struct[52],
            'Armor Break': prize_struct[53],
            'Mental Break': prize_struct[54],
            'Confuse': prize_struct[55],
            'Berserk': prize_struct[56],
            'Provoke': prize_struct[57],
            'Threaten': prize_struct[58],
            'Sleep': prize_struct[59],
            'Silence': prize_struct[60],
            'Dark': prize_struct[61],
            'Protect': prize_struct[62],
            'Shell': prize_struct[63],
            'Reflect': prize_struct[64],
            'Nulblaze': prize_struct[65],
            'Nulfrost': prize_struct[66],
            'Nulshock': prize_struct[67],
            'Nultide': prize_struct[68],
            'Regen': prize_struct[69],
            'Haste': prize_struct[70],
            'Slow': prize_struct[71],
        }
        if prize_struct[72] == 2:
            data['Undead'] = True
        else:
            data['Undead'] = False
        if prize_struct[74] == 32:
            data['Auto-statuses'].append('Reflect')
        elif prize_struct[74] == 192:
            data['Auto-statuses'].append('Nulall')
        elif prize_struct[74] == 32 + 192:
            data['Auto-statuses'].append('Reflect')
            data['Auto-statuses'].append('Nulall')
        if prize_struct[75] == 3:
            data['Auto-statuses'].append('???')
        elif prize_struct[75] == 4:
            data['Auto-statuses'].append('Regen')
        elif prize_struct[75] == 3 + 4:
            data['Auto-statuses'].append('???')
            data['Auto-statuses'].append('Regen')
        if data['Auto-statuses'] == []:
            data['Auto-statuses'].append('None')
        # check if the monster can drop equipment
        if prize_struct[174] == 1:
            data['Equipment'] = {
                'Drop chance': prize_struct[139],
                'Bonus critical chance': prize_struct[175],
                'Base damage': prize_struct[176],
                'Slots range': [],
                'Max ability rolls range': [],
                'Ability arrays': {},
            }
            for i in range(8):
                slots_mod = prize_struct[173] + i - 4
                slots = ((slots_mod + ((slots_mod >> 31) & 3)) >> 2)
                slots = self.ffx_info._fix_out_of_bounds_value(slots)
                data['Equipment']['Slots range'].append(str(slots))
                ab_mod = prize_struct[177] + i - 4
                ab_rolls = (ab_mod + ((ab_mod >> 31) & 7)) >> 3
                data['Equipment']['Max ability rolls range'].append(
                    str(ab_rolls))
            data['Equipment']['Ability arrays'] = {
                'Tidus': get_abilities(178),
                'Yuna': get_abilities(210),
                'Auron': get_abilities(242),
                'Kimahri': get_abilities(274),
                'Wakka': get_abilities(306),
                'Lulu': get_abilities(338),
                'Rikku': get_abilities(370),
            }
        else:
            data['Equipment'] = 'None'
        return data

    def print_monster_data(self):

        def treeview(item, padding=0, string=''):
            if isinstance(item, list):
                string += f': {", ".join(item)}'
                return string
            elif not isinstance(item, dict):
                string += f': {str(item)}'
                return string
            else:
                for key in item:
                    string += f'\n{"    " * padding}{str(key)}'
                    if not isinstance(item, list):
                        string += treeview(item[key], padding + 1)
            return string

        monster_index = self.monster_data_widget['listbox'].curselection()
        try:
            monster_index = monster_index[0]
        except IndexError:
            return
        prize_struct = self.monsters_data[self.monsters_names[monster_index]]
        data = self.get_monster_data(prize_struct)

        data_string = treeview(data)[1:] + '\n\n'

        # print raw data
        for index, byte in enumerate(prize_struct):
            # every 16 bytes make a new line
            if index % 16 == 0:
                data_string += '\n'
                data_string += ' '.join(
                    [f'[{hex(index + i)[2:]:>3}]' for i in range(16)])
                data_string += '\n'
            # print the bytes' value
            # data += f' {hex(byte)[2:]:>3}  '
            data_string += f' {byte:>3}  '
            # sections
            if index == 0x80 - 1:
                data_string += '\nPrize struct'
            elif index == 0xB0 - 1:
                data_string += '\n             start of equipment'
            elif index == 0x190 - 1:
                data_string += '\n             end of equipment'

        self.monster_data_widget['text'].config(state='normal')
        self.monster_data_widget['text'].delete(1.0, 'end')
        self.monster_data_widget['text'].insert(1.0, data_string)
        self.monster_data_widget['text'].config(state='disabled')

    def make_monster_data_widget(self):

        widget = {}
        widget['scrollbar'] = tk.Scrollbar(self)
        widget['scrollbar'].pack(fill='y', side='right')

        widget['text'] = tk.Text(self, font=self.main_font, width=55)
        widget['text'].pack(expand=True, fill='both', side='right')
        widget['text'].config(
            yscrollcommand=widget['scrollbar'].set)

        widget['scrollbar'].config(command=widget['text'].yview)

        widget['listvar'] = tk.StringVar(value=self.monsters_names)
        widget['listbox'] = tk.Listbox(
            self, width=30, listvariable=widget['listvar'])
        widget['listbox'].bind(
            '<<ListboxSelect>>', lambda _: self.print_monster_data())

        widget['listbox'].pack(fill='y', side='left')

        return widget


class FFXDamageRNGTrackerUI(tk.Frame):
    '''Widget used to track damage rolls, critical chance
    and escape chance rng.
    '''

    def __init__(self, parent, rng_tracker, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.rng_tracker = rng_tracker
        self.main_font = font.Font(family='Courier New', size=9)

        # when the mouse enters the parent widget it binds the mousewheel
        self.bind(
            '<Enter>',
            lambda _: self.bind_all('<MouseWheel>', self.on_mousewheel))
        # when the mouse leaves the parent widget it unbinds the mousewheel
        self.bind(
            '<Leave>', lambda _: self.unbind_all('<MouseWheel>'))

        for i in range(1, 9):
            self.columnconfigure(i, weight=1)
        self.rowconfigure(1, weight=1)

        self.monster_names = sorted(
            list(self.rng_tracker.monsters_data.keys()))

        self.possible_stats = self.get_possible_stat_values()

        self.encounters = self.make_labeled_spinbox(
            'Encounters:', self, 0, 0,
            from_=0, to=1000, command=self.update_tracker)
        self.preemptives = self.make_labeled_spinbox(
            'Preemptives/ambushes:', self, 0, 2,
            from_=0, to=1000, command=self.update_tracker)
        tk.Label(self, text='Monster:').grid(row=0, column=4, sticky='e')
        self.monster = tk.Spinbox(
            self, values=self.monster_names,
            command=self.get_monster_stats)
        self.monster.grid(row=0, column=5, sticky='w')
        self.monster.bind('<KeyRelease>', lambda _: self.get_monster_stats())
        self.monster_luck = self.make_labeled_spinbox(
            'Enemy Luck:', self, 0, 6,
            values=self.possible_stats['luck'], command=self.update_tracker)
        self.monster_evasion = self.make_labeled_spinbox(
            'Enemy Evasion:', self, 0, 8,
            values=self.possible_stats['evasion'], command=self.update_tracker)

        self.character_trackers = self.make_character_trackers(1, 10)

        # initialize the ui
        self.encounters.set(2)
        self.character_trackers['tidus']['actions']['attack'].set(3)
        self.character_trackers['auron']['actions']['attack'].set(3)
        self.monster.delete(0, 'end')
        self.monster.insert(0, 'sinspawn_ammes')
        self.get_monster_stats()

    def make_character_trackers(self, row: int, columnspan: int):

        def make_character_tracker(parent, index: int):
            '''Setup spinboxes and a text to track character rng.'''
            def get_damage_rng_position():
                '''Get the damage rng position based on character index
                and number of actions.
                '''
                actions = tracker['actions']
                position = int(self.encounters.get())
                position -= int(self.preemptives.get())

                if position < 0:
                    position = 0

                if index > 6:
                    position = position * 11

                position += int(actions['attack'].get()) * 2

                if index == 0:
                    position += int(actions['haste'].get())
                    position += int(actions['armor_break'].get()) * 2
                    position += int(actions['spiral_cut'].get()) * 4
                elif index == 1:
                    position += int(actions['cure'].get())
                elif index == 2:
                    position += int(actions['power_break'].get()) * 2
                    position += int(actions['overdrive'].get()) * 4
                elif index == 3:
                    position += int(actions['lancet'].get()) * 2
                    position += int(actions['grenade'].get()) * 2
                    position += int(actions['tier_2_grenade'].get())
                    position += int(actions['overdrive'].get()) * 2
                elif index == 4:
                    position += int(actions['dark_attack'].get()) * 2
                    position += int(actions['elemental_reels'].get())
                elif index == 5:
                    position += int(actions['magic'].get())
                    position += int(actions['elemental_fury'].get()) * 16
                elif index == 6:
                    position += int(actions['grenade'].get()) * 2
                    position += int(actions['tier_2_grenade'].get())
                    position += int(actions['aoe_mix'].get()) * 2
                    position += int(actions['9_hit_mix'].get()) * 9
                elif index == 7:
                    position += int(actions['special_attack'].get()) * 2
                    position += int(actions['magic'].get())
                    position += int(actions['overdrive'].get())

                position += int(actions['healing_item'].get())
                position += int(actions['escape'].get())
                position += int(actions['manual_rng'].get())

                return position

            def get_hit_rng_position():
                '''Get the hit rng position based on character index
                and number of actions.
                '''
                actions = tracker['actions']

                position = 0

                position += int(actions['attack'].get())

                if index == 0:
                    position += int(actions['armor_break'].get())
                elif index == 2:
                    position += int(actions['power_break'].get())
                elif index == 4:
                    position += int(actions['dark_attack'].get())

                position += int(actions['miss'].get())

                return position

            def spinbox_command():
                '''Update the text based on the spinboxes values.'''
                damage_rng_position = get_damage_rng_position()
                damage_rng = self.rng_tracker.rng_arrays[20 + index]
                hit_rng_position = get_hit_rng_position()
                hit_rng = self.rng_tracker.rng_arrays[36 + index]
                luck = int(tracker['luck'].get())
                target_luck = int(self.monster_luck.get())
                equipment_crit = int(tracker['equipment_crit'].get())
                evasion = int(self.monster_evasion.get())
                accuracy = int(tracker['accuracy'].get())

                crit_chance = luck - target_luck + equipment_crit
                od_crit_chance = luck - target_luck

                # similar to accuracy * 4 // 10
                accuracy = accuracy * 2
                accuracy = (accuracy * 0x66666667) // 0xffffffff
                accuracy = accuracy // 2
                hit_chance_index = accuracy // 0xffffffffffffffffffffffffff
                hit_chance_index += accuracy - evasion + 10
                if hit_chance_index < 0:
                    hit_chance_index = 0
                elif hit_chance_index > 8:
                    hit_chance_index = 8
                hit_chance_table = (25, 30, 30, 40, 40, 50, 50, 80, 100)
                hit_chance = hit_chance_table[hit_chance_index]
                hit_chance += luck - target_luck

                data = []

                for i in range(0, 40):

                    if i % 2 == 0:
                        result = [f'[{(i // 2) + 1:2}]']
                    else:
                        result = ['    ']

                    damage_roll = damage_rng[damage_rng_position + i] & 31
                    result.append(f'{damage_roll:>2}/31')

                    crit_roll = damage_rng[damage_rng_position + i + 1] % 101
                    if crit_roll < crit_chance:
                        result.append('C')
                    else:
                        result.append(' ')
                    if crit_roll < od_crit_chance:
                        result.append('ODC')
                    else:
                        result.append('   ')

                    escape_roll = damage_rng[damage_rng_position + i] & 255
                    if escape_roll < 191:
                        result.append('E')
                    else:
                        result.append(' ')

                    hit_roll = hit_rng[hit_rng_position + (i // 2)] % 101
                    if hit_chance > hit_roll:
                        result.append(' ')
                    else:
                        result.append('M')

                    data.append('|'.join(result))

                data = '\n'.join(data)
                tracker['text'].config(state='normal')
                tracker['text'].delete(1.0, 'end')
                tracker['text'].insert(1.0, data)
                tracker['text'].config(state='disabled')

            tracker = {
                'spinbox_command': spinbox_command,
                'frame': tk.Frame(parent),
                'actions': {},
            }

            tracker['frame'].grid(row=0, column=index, sticky='nsew')

            if index < 7:
                character = self.rng_tracker.CHARACTERS[index]
            elif index == 7:
                character = 'Aeons'

            tk.Label(tracker['frame'], text=character).grid(
                row=0, column=0, columnspan=2, sticky='we')

            actions = {
                'attack': ('Attack', 1)
            }

            if index == 0:
                actions['haste'] = ('Haste', 2)
                actions['armor_break'] = ('Armor Break', 3)
                actions['spiral_cut'] = ('Spiral Cut', 4)
            elif index == 1:
                actions['cure'] = ('Cure', 2)
            elif index == 2:
                actions['power_break'] = ('Power Break', 2)
                actions['overdrive'] = ('Overdrive', 3)
            elif index == 3:
                actions['lancet'] = ('Lancet', 2)
                actions['grenade'] = ('Grenade', 3)
                actions['tier_2_grenade'] = ('Tier 2 Grenade', 4)
                actions['overdrive'] = ('Overdrive', 5)
            elif index == 4:
                actions['dark_attack'] = ('Dark Attack', 2)
                actions['elemental_reels'] = ('Elemental Reels', 3)
            elif index == 5:
                actions['magic'] = ('ST Magic', 2)
                actions['elemental_fury'] = ('Elemental Fury', 3)
            elif index == 6:
                actions['grenade'] = ('Grenade', 2)
                actions['tier_2_grenade'] = ('Tier 2 Grenade', 3)
                actions['aoe_mix'] = ('AoE Damage Mix', 4)
                actions['9_hit_mix'] = ('9-Hit Mix', 5)
            else:
                actions['special_attack'] = ('Special Attack', 2)
                actions['magic'] = ('ST Magic', 3)
                actions['overdrive'] = ('Overdrive', 4)

            actions['miss'] = ('Miss', 16)
            actions['healing_item'] = ('Healing Item', 17)
            actions['escape'] = ('Escape', 18)
            actions['manual_rng'] = ('Manual RNG', 19)

            for key, value in actions.items():
                tracker['actions'][key] = self.make_labeled_spinbox(
                    value[0], tracker['frame'], value[1], 0, from_=0, to=1000,
                    command=spinbox_command)

            for row in range(len(actions) + 1, 10):
                tk.Label(tracker['frame'], text='').grid(row=row, column=0)

            tracker['text'] = tk.Text(
                tracker['frame'], font=self.main_font, state='disabled')
            tracker['text'].grid(row=20, column=0, columnspan=2, sticky='nsew')

            tracker['accuracy'] = self.make_labeled_spinbox(
                'Accuracy', tracker['frame'], 21, 0, from_=0, to=255,
                command=spinbox_command)
            base_accuracy = (10, 3, 3, 5, 25, 3, 5, 14)
            tracker['accuracy'].set(base_accuracy[index])

            tracker['luck'] = self.make_labeled_spinbox(
                'Luck', tracker['frame'], 22, 0, from_=0, to=255,
                command=spinbox_command)
            base_luck = (18, 17, 17, 18, 19, 17, 18, 17)
            tracker['luck'].set(base_luck[index])

            tracker['equipment_crit'] = self.make_labeled_spinbox(
                'Equipment Crit', tracker['frame'], 23, 0, from_=0, to=1000,
                command=spinbox_command)
            default_equipment_crit = (6, 6, 6, 3, 3, 6, 6, 6)
            tracker['equipment_crit'].set(default_equipment_crit[index])

            tracker['frame'].columnconfigure(1, weight=1)
            tracker['frame'].rowconfigure(20, weight=1)

            return tracker

        trackers = {}

        frame = tk.Frame(self)
        frame.grid(row=row, column=0, columnspan=columnspan, sticky='nsew')
        frame.rowconfigure(0, weight=1)

        characters = (
            'tidus', 'yuna', 'auron', 'kimahri',
            'wakka', 'lulu', 'rikku', 'aeons'
        )

        for index, character in enumerate(characters):
            trackers[character] = make_character_tracker(
                frame, index)

        for i in range(len(characters)):
            frame.columnconfigure(i, weight=1)

        return trackers

    def make_labeled_spinbox(self, text, parent, row, column, **kwargs):
        tk.Label(parent, text=text).grid(row=row, column=column, sticky='e')
        spinbox = BetterSpinbox(parent, **kwargs)
        spinbox.grid(row=row, column=column + 1, sticky='w')
        return spinbox

    def on_mousewheel(self, event):
        '''If the widget under the cursor is a spinbox,
        it increments/decrements it on wheelup/wheeldown.
        '''
        # get widget under cursor
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        # increment or decrement based on scroll direction
        if (isinstance(widget, BetterSpinbox)
                or isinstance(widget, tk.Spinbox)):
            if event.delta == 120:
                widget.invoke('buttonup')
            elif event.delta == -120:
                widget.invoke('buttondown')

    def update_tracker(self):
        '''Update every character's text.'''
        for tracker in self.character_trackers.values():
            tracker['spinbox_command']()

    def get_monster_stats(self):
        '''Get a monster's Luck stat from it's prize struct.'''
        name = self.monster.get()
        try:
            prize_struct = self.rng_tracker.monsters_data[name]
        except KeyError:
            return
        luck = prize_struct[37]
        evasion = prize_struct[38]
        if luck < 1:
            luck = 1
        if evasion < 1:
            evasion = 1
        self.monster_luck.set(luck)
        self.monster_evasion.set(evasion)
        self.update_tracker()

    def get_possible_stat_values(self):
        # using sets avoid duplicates
        stats = {
            'luck': {1},
            'evasion': {1},
        }
        # get the value of each stat from every enemy
        for prize_struct in self.rng_tracker.monsters_data.values():
            stats['luck'].add(prize_struct[37])
            stats['evasion'].add(prize_struct[38])

        # sort the values from lowest to highest
        possible_stats = {}
        for stat, values in stats.items():
            possible_stats[stat] = sorted(values)
        return possible_stats


class FFXRNGTrackerUI():
    '''Widget that contains all the other RNG tracking widgets.'''

    def __init__(self, parent, rng_tracker):
        self.parent = parent
        self.rng_tracker = rng_tracker
        self.notebook = ttk.Notebook(self.parent)
        self.notebook.pack(expand=True, fill='both')

        self.seed_info_page = FFXSeedInfoUI(self.notebook, self.rng_tracker)
        self.notebook.add(self.seed_info_page, text='Seed info')

        self.drops_tracker_page = FFXDropsRNGTrackerUI(
            self.notebook, self.rng_tracker)
        self.notebook.add(self.drops_tracker_page, text='Drops')

        self.encounters_tracker_page = FFXEncountersRNGTrackerUI(
            self.notebook, self.rng_tracker)
        self.notebook.add(self.encounters_tracker_page, text='Encounters')

        self.damage_tracker_page = FFXDamageRNGTrackerUI(
            self.notebook, self.rng_tracker)
        self.notebook.add(
            self.damage_tracker_page, text='Damage/crits/escapes/misses')

        self.status_tracker_page = FFXStatusRNGTrackerUI(
            self.notebook, self.rng_tracker)
        self.notebook.add(self.status_tracker_page, text='Status')

        self.monster_data_viewer_page = FFXMonsterDataViewerUI(
            self.notebook, self.rng_tracker)
        self.notebook.add(self.monster_data_viewer_page, text='Monster Data')


class DamageRollsDialogue(simpledialog.Dialog):
    '''Input dialogue used to get damage rolls.'''

    def __init__(self, *args, **kwargs):
        self.warning_label = False
        super().__init__(*args, **kwargs)

    def body(self, parent):
        tk.Label(parent, text='Damage rolls (Auron1 Tidus1 A2 T2 A3 T3)').pack()
        self.entry = tk.Entry(parent, width=25)
        self.entry.pack(fill='x')
        return self.entry

    def buttonbox(self):
        tk.Button(self, text='Submit', command=self.validate_input).pack()
        self.bind('<Return>', lambda _: self.validate_input())
        self.bind('<Escape>', lambda _: on_ui_close(self.parent))

    def validate_input(self):
        input_string = self.entry.get()
        # replace different symbols with spaces
        for symbol in (',', '-', '/', '\\'):
            input_string = input_string.replace(symbol, ' ')
        # fixes double spaces
        damage_rolls = ' '.join(input_string.split())
        damage_rolls = damage_rolls.split(' ')
        try:
            damage_rolls = [int(damage_roll) for damage_roll in damage_rolls]
        except ValueError as error:
            error = str(error).split(':', 1)[1]
            self.show_warning(f'{error} is not a valid damage roll.')
            return
        if len(damage_rolls) < 6:
            self.show_warning('Need at least 6 damage rolls.')
            return
        elif len(damage_rolls) > 6:
            self.show_warning(
                f'Submitted too many values: {len(damage_rolls)}')
            return
        try:
            self.rng_tracker = FFXRNGTracker(damage_rolls)
        except (FFXRNGTracker.InvalidDamageRollError,
                FFXRNGTracker.SeedNotFoundError) as error:
            self.show_warning(error)
            return

        print('Damage rolls: ', ', '.join([str(i) for i in damage_rolls]))

        self.destroy()

    def show_warning(self, text):
        if self.warning_label:
            self.warning_label.config(text=text)
        else:
            self.warning_label = tk.Label(self, text=text)
            self.warning_label.pack(fill='x')


def on_ui_close(main_window):
    '''Called when the main window is closed.'''
    main_window.quit()
    quit()


def main(widget, title='ffx_rng_tracker', size='1280x830'):
    '''Creates a Tkinter main window, initializes the rng tracker
    and passes them to the rng tracking widget.
    '''
    root = tk.Tk()
    root.withdraw()
    entry_widget = DamageRollsDialogue(root, title=title)
    try:
        rng_tracker = entry_widget.rng_tracker
    except AttributeError:
        on_ui_close(root)

    root.protocol(
        'WM_DELETE_WINDOW', lambda: on_ui_close(root))
    root.title(title)
    root.geometry(size)

    ui = widget(root, rng_tracker)

    root.deiconify()
    root.mainloop()


if __name__ == '__main__':
    main(FFXRNGTrackerUI)
