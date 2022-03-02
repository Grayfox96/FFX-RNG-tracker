import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable

from ..configs import Configs
from ..data.constants import EncounterCondition
from ..data.encounter_formations import FORMATIONS
from ..data.encounters import ANY_ENCOUNTERS
from ..events.comment import Comment
from ..events.encounter import (Encounter, MultizoneRandomEncounter,
                                RandomEncounter)
from ..events.main import Event
from ..events.parsing import parse_encounter
from .base_widgets import (BaseWidget, BetterSpinbox, BetterText,
                           ScrollableFrame)


@dataclass
class EncountersTrackerInputWidget:
    initiative_equip: ttk.Checkbutton
    current_zone: tk.StringVar
    scales: dict[str, tk.Scale]


class EncountersTracker(BaseWidget):
    """Widget used to track encounters RNG."""

    def make_input_widget(self) -> EncountersTrackerInputWidget:
        outer_frame = tk.Frame(self)
        outer_frame.pack(fill='y', side='left')
        outer_frame.rowconfigure(index=1, weight=1)
        initiative_equip = ttk.Checkbutton(
            outer_frame, text='Sentry', command=self.parse_input)
        initiative_equip.grid(row=0, column=0, sticky='w')
        initiative_equip.state(['selected'])
        current_zone = tk.StringVar(value='Start')
        frame = ScrollableFrame(outer_frame)
        frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
        start = tk.Radiobutton(
            frame, text='Start', variable=current_zone,
            value='Start', command=self.parse_input)
        start.grid(row=0, column=1, sticky='w')
        scales = {}
        for row, encounter in enumerate(ANY_ENCOUNTERS, start=1):
            if encounter['type'] == 'set':
                continue
            scale = tk.Scale(
                frame, orient='horizontal', label=None,
                from_=encounter['min'], to=encounter['max'],
                command=lambda _: self.parse_input())
            scale.set(encounter['default'])
            scale.grid(row=row, column=0)
            label = tk.Radiobutton(
                frame, text=encounter['label'], variable=current_zone,
                value=encounter['label'], command=self.parse_input)
            label.grid(row=row, column=1, sticky='sw')
            scales[encounter['label']] = scale
        widget = EncountersTrackerInputWidget(
            initiative_equip=initiative_equip,
            current_zone=current_zone,
            scales=scales,
            )
        return widget

    def get_tags(self) -> dict[str, str]:
        important_monsters = '(?i)' + '|'.join(Configs.important_monsters)
        tags = {
            'wrap margin': '^.+$',
            'preemptive': 'Preemptive',
            'ambush': 'Ambush',
            'important monster': important_monsters,
        }
        return tags

    def get_parsing_functions(self) -> dict[str, Callable[..., Event]]:
        parsing_functions = {
            'encounter': parse_encounter,
        }
        return parsing_functions

    def get_default_input_text(self) -> str:
        return self.get_input()

    def get_input(self) -> str:
        initiative_equip = self.input_widget.initiative_equip.state()
        initiative_equip = 'selected' in initiative_equip

        spacer = '#' + ('=' * 60)
        input_data = []
        for encounter in ANY_ENCOUNTERS:
            if initiative_equip:
                initiative = encounter['initiative']
            else:
                initiative = 'false'
            if encounter['type'] == 'set':
                encs = 1
            else:
                encs = self.input_widget.scales[encounter['label']].get()
                if encs > 0:
                    input_data.append(spacer)
                    input_data.append(f'#     {encounter["label"]}:')
            for _ in range(encs):
                line = ' '.join([
                    'encounter',
                    encounter['type'],
                    encounter['name'],
                    initiative,
                    encounter['forced_condition'],
                ])
                input_data.append(line)
        return '\n'.join(input_data)

    def parse_input(self) -> None:
        self.gamestate.reset()
        events_sequence = self.parser.parse(self.get_input())

        output_data = []
        for event in events_sequence:
            match event:
                case RandomEncounter():
                    line = str(event)
                    output_data.append(
                        line[10:21] + line[23 + len(event.zone):])
                case MultizoneRandomEncounter():
                    zones = '/'.join(event.zones)
                    line = str(event)
                    output_data.append(
                        line[10:21] + line[23 + len(zones):])
                case Encounter():
                    output_data.append(str(event)[10:])
                case _:
                    output_data.append(str(event)[1:])

        data = '\n'.join(output_data)
        current_zone = self.input_widget.current_zone.get()
        index = data.find(current_zone)
        if index > 0:
            data = data[index - 5:]

        self.print_output(data)


@dataclass
class EncountersPlannerInputWidget:
    initiative_equip: ttk.Checkbutton
    current_zone: tk.IntVar
    scales: list[tuple[str, tk.Scale]]
    highlight: tk.StringVar


class EncountersPlanner(EncountersTracker):

    def make_input_widget(self) -> EncountersPlannerInputWidget:
        outer_frame = tk.Frame(self)
        outer_frame.pack(fill='y', side='left')
        outer_frame.rowconfigure(index=10, weight=1)

        highlight = tk.StringVar(outer_frame, value='Type monster names here')
        entry = ttk.Entry(outer_frame, textvariable=highlight)
        entry.pack(fill='x')
        entry.bind('<KeyRelease>', lambda _: self.parse_input())

        options = ['Boss', 'Simulation']
        options.extend([z.name for z in FORMATIONS.zones.values()])
        textvariable = tk.StringVar(outer_frame)
        textvariable.set(options[0])
        combobox = ttk.Combobox(
            outer_frame, values=options, state='readonly',
            textvariable=textvariable)
        combobox.pack(fill='x')
        button = tk.Button(
            outer_frame, text='Add Slider',
            command=lambda: self.add_scale(
                textvariable.get(), inner_frame, current_zone
                ),
            )
        button.pack(fill='x', anchor='n')

        initiative_equip = ttk.Checkbutton(
            outer_frame, text='Initiative', command=self.parse_input)
        initiative_equip.pack(fill='x', anchor='w')
        initiative_equip.state(['selected'])

        current_zone = tk.IntVar(value=0)
        inner_frame = ScrollableFrame(outer_frame)
        inner_frame.pack(expand=True, fill='both')

        widget = EncountersPlannerInputWidget(
            initiative_equip=initiative_equip,
            current_zone=current_zone,
            scales=[],
            highlight=highlight,
        )
        return widget

    def get_input(self) -> str:
        initiative_equip = self.input_widget.initiative_equip.state()
        initiative_equip = 'selected' in initiative_equip
        initiative = 'true' if initiative_equip else 'false'

        current_zone_index = self.input_widget.current_zone.get()

        spacer = '#' + ('=' * 60)
        input_data = []
        for index, (name, scale) in enumerate(self.input_widget.scales):
            name = name.lower().replace(' ', '_')
            match name:
                case 'boss':
                    name = 'lord_ochu'
                    encounter_type = 'set_optional'
                    forced_condition = ''
                case 'simulation':
                    name = 'simulation_(mi\'ihen)'
                    encounter_type = 'simulated'
                    forced_condition = 'normal'
                case _:
                    name = name
                    encounter_type = 'random'
                    forced_condition = ''
            for count in range(scale.get()):
                if count == 0:
                    input_data.append(spacer)
                    if index == current_zone_index:
                        input_data.append('///')
                    try:
                        input_data.append(
                            f'#     {FORMATIONS.zones[name].name}')
                    except KeyError:
                        pass
                line = (f'encounter {encounter_type} {name} {initiative} '
                        f'{forced_condition}')
                input_data.append(line)

        return '\n'.join(input_data)

    def parse_input(self):
        self.gamestate.reset()
        events_sequence = self.parser.parse(self.get_input())

        output_data = []
        monsters_tally = {}
        for event in events_sequence:
            match event:
                # if the text contains /// it hides the lines before it
                case Comment() if event.text == '///':
                    output_data.clear()
                case Comment():
                    output_data.append(str(event)[1:])
                case RandomEncounter():
                    line = str(event)
                    line = line[10:21] + line[23 + len(event.zone):]
                    index = 0
                    for monster in event.formation:
                        tally = monsters_tally.get(monster.name, 0) + 1
                        monsters_tally[monster.name] = tally
                        index = (line.index(monster.name, index)
                                 + len(monster.name))
                        line = line[:index] + f'[{tally}]' + line[index:]
                    output_data.append(line)
                case _:
                    output_data.append(str(event)[10:])

        data = '\n'.join(output_data)
        data = data.replace('Lord Ochu [Lord Ochu]', 'Boss')
        data = data.replace('(Mi\'ihen) (Bomb or Dual Horn)', '')

        self.print_output(data)
        captured_monsters = [m for m, n in monsters_tally.items() if n >= 10]
        needle = '(?i)' + '|'.join(captured_monsters)
        self.output_widget.highlight_pattern(needle, 'encounter')
        important_monsters = self.input_widget.highlight.get().split(',')
        needle = '(?i)' + '|'.join([m.strip() for m in important_monsters])
        self.output_widget.highlight_pattern(needle, 'important monster')

    def add_scale(
            self, text: str, parent: tk.Frame,
            variable=tk.IntVar) -> None:
        index = len(self.input_widget.scales)
        scale = tk.Scale(
            parent, orient='horizontal', label=None, from_=0, to=100,
            command=lambda _: self.parse_input())
        scale.grid(row=index, column=0, sticky='w')
        label = tk.Radiobutton(
            parent, text=text, variable=variable, value=index,
            command=self.parse_input)
        label.grid(row=index, column=1, sticky='sw')
        self.input_widget.scales.append((text, scale))


@dataclass
class EncounterTableInputWidget:
    highlight: tk.StringVar
    initiative_equip: ttk.Checkbutton
    random_encounters: BetterSpinbox
    forced_encounters: BetterSpinbox
    simulated_encounters: BetterSpinbox
    encounters: BetterSpinbox
    zones: dict[str, tk.BooleanVar]


class EncountersTable(BaseWidget):
    """"""

    def __init__(self, parent, *args, **kwargs):
        self.paddings = self.get_paddings()
        super().__init__(parent, *args, **kwargs)

    def make_input_widget(self) -> EncounterTableInputWidget:
        outer_frame = tk.Frame(self)
        outer_frame.pack(fill='y', side='left')
        outer_frame.rowconfigure(index=10, weight=1)

        highlight = tk.StringVar(outer_frame, value='Type monster names here')
        entry = ttk.Entry(outer_frame, textvariable=highlight)
        entry.grid(row=0, column=0, columnspan=2, sticky='nsew')
        entry.bind('<KeyRelease>', lambda _: self.parse_input())

        initiative_equip = ttk.Checkbutton(
            outer_frame, text='Initiative', command=self.parse_input)
        initiative_equip.grid(row=1, column=0, sticky='nsew')
        initiative_equip.state(['selected'])

        tk.Label(outer_frame, text='Random Encounters').grid(row=2, column=0)
        random_encounters = BetterSpinbox(
            outer_frame, from_=0, to=2000, command=self.parse_input)
        random_encounters.grid(row=2, column=1)

        tk.Label(outer_frame, text='Forced Encounters').grid(row=3, column=0)
        forced_encounters = BetterSpinbox(
            outer_frame, from_=0, to=2000, command=self.parse_input)
        forced_encounters.grid(row=3, column=1)

        tk.Label(outer_frame, text='Simulated Encounters').grid(
            row=4, column=0)
        simulated_encounters = BetterSpinbox(
            outer_frame, from_=0, to=2000, command=self.parse_input)
        simulated_encounters.grid(row=4, column=1)

        tk.Label(outer_frame, text='Encounters to show').grid(row=11, column=0)
        encounters = BetterSpinbox(
            outer_frame, from_=0, to=2000, command=self.parse_input)
        encounters.grid(row=11, column=1)
        encounters.set(20)

        inner_frame = ScrollableFrame(outer_frame)
        inner_frame.grid(row=10, column=0, columnspan=2, sticky='nsew')

        zones = {}
        for zone, data in FORMATIONS.zones.items():
            zone_var = tk.BooleanVar(inner_frame, value=False)
            checkbutton = ttk.Checkbutton(
                inner_frame, text=data.name, command=self.parse_input,
                variable=zone_var)
            checkbutton.pack(anchor='w', fill='x')
            zones[zone] = zone_var

        widget = EncounterTableInputWidget(
            highlight=highlight,
            initiative_equip=initiative_equip,
            random_encounters=random_encounters,
            forced_encounters=forced_encounters,
            simulated_encounters=simulated_encounters,
            encounters=encounters,
            zones=zones,
        )
        return widget

    def make_output_widget(self) -> BetterText:
        widget = super().make_output_widget()
        widget.configure(wrap='none')
        widget._add_h_scrollbar()
        return widget

    def get_tags(self) -> dict[str, str]:
        tags = {
            'wrap margin': '^.+$',
            'preemptive': 'Preemptive',
            'ambush': 'Ambush',
        }
        return tags

    def get_parsing_functions(self) -> dict[str, Callable[..., Event]]:
        parsing_functions = {
            'encounter': parse_encounter,
        }
        return parsing_functions

    def get_default_input_text(self) -> str:
        return self.get_input()

    def get_input(self) -> str:
        initiative_equip = self.input_widget.initiative_equip.state()

        if 'selected' in initiative_equip:
            initiative = 'true'
        else:
            initiative = 'false'

        zones = []
        for zone, active in self.input_widget.zones.items():
            if active.get():
                zones.append(zone)

        input_data = []
        for _ in range(int(self.input_widget.forced_encounters.get())):
            input_data.append(f'encounter set lord_ochu {initiative} normal')
        for _ in range(int(self.input_widget.random_encounters.get())):
            input_data.append(f'encounter random besaid_lagoon {initiative}')
        for _ in range(int(self.input_widget.simulated_encounters.get())):
            input_data.append(f'encounter simulated simulation_(mi\'ihen) '
                              f'{initiative} normal')
        for _ in range(int(self.input_widget.encounters.get())):
            if zones:
                input_data.append(f'encounter multizone {"/".join(zones)} '
                                  f'{initiative}')

        return '\n'.join(input_data)

    def parse_input(self) -> None:
        self.gamestate.reset()
        events_sequence = self.parser.parse(self.get_input())

        output_data = []
        for event in events_sequence:
            match event:
                case MultizoneRandomEncounter():
                    if not output_data:
                        zones = []
                        for zone in event.zones:
                            zone_name = FORMATIONS.zones[zone].name
                            padding = self.paddings[zone]
                            zones.append(f'{zone_name:{padding}}')
                        first_line = (' ' * 26) + ''.join(zones)
                        output_data.append(first_line)
                        output_data.append('=' * len(first_line))
                    for count, enc in enumerate(event.encounters):
                        # append a spacer before appending encounters
                        # but only if there is already data
                        if output_data and count == 0:
                            enc = event.encounters[0]
                            if enc.condition == EncounterCondition.NORMAL:
                                condition = ''
                            else:
                                condition = enc.condition
                            line = (f'{enc.index:4}|{enc.random_index:4}|'
                                    f'{enc.zone_index:3}: {condition:10} ')
                        formation = ', '.join([str(m) for m in enc.formation])
                        line += f'{formation:{self.paddings[enc.zone]}}'
                    output_data.append(line)

        self.print_output('\n'.join(output_data))
        important_monsters = self.input_widget.highlight.get().split(',')
        needle = '(?i)' + '|'.join([m.strip() for m in important_monsters])
        self.output_widget.highlight_pattern(needle, 'important monster')

    def get_paddings(self) -> dict[str, int]:
        paddings = {}
        for zone, data in FORMATIONS.zones.items():
            padding = len(zone)
            for f in data.formations:
                padding = max(padding, len(', '.join([str(m) for m in f])))
            paddings[zone] = padding + 1
        return paddings
