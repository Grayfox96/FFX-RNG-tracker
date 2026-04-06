import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Literal

from ..configs import UIWidgetConfigs
from ..data.encounter_formations import ZONES
from ..events.parser import EventParser
from ..ui_abstract.encounters_table import EncountersTable
from .base_widgets import BetterSpinbox, ScrollableFrame
from .tkinter_utils import create_command_proxy
from .tktracker import TkTracker


class TkEncountersTableInputWidget(ttk.Frame):
    """"""
    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.initiative_button = ttk.Checkbutton(self, text='Initiative')
        self.initiative_button.grid(row=0, column=0, sticky='w')
        self.initiative_button.invoke()

        ttk.Label(self, text='Encounters to show').grid(row=1, column=0)
        self.shown_encounters = BetterSpinbox(self, from_=0, to=2000)
        self.shown_encounters.grid(row=1, column=1, sticky='w')
        self.shown_encounters.set(20)

        ttk.Label(self, text='Start from').grid(row=2, column=0)
        self.starting_encounter = BetterSpinbox(self, from_=-2000, to=2000)
        self.starting_encounter.grid(row=2, column=1, sticky='w')

        ttk.Label(self, text='Random Encounters').grid(row=3, column=0)
        self.random_encounters = BetterSpinbox(self, from_=0, to=2000)
        self.random_encounters.grid(row=3, column=1, sticky='w')

        ttk.Label(self, text='Bosses').grid(row=4, column=0)
        self.forced_encounters = BetterSpinbox(self, from_=0, to=2000)
        self.forced_encounters.grid(row=4, column=1, sticky='w')

        ttk.Label(self, text='Simulated Encounters').grid(row=5, column=0)
        self.simulated_encounters = BetterSpinbox(self, from_=0, to=2000)
        self.simulated_encounters.grid(row=5, column=1, sticky='w')

        zones_frame = ScrollableFrame(self)
        zones_frame.grid(row=10, column=0, columnspan=2, sticky='nsew')
        self.rowconfigure(10, weight=1)
        self.columnconfigure(1, weight=1)

        self.zones_buttons: dict[str, ttk.Checkbutton] = {}
        self.zones: dict[str, tk.BooleanVar] = {}
        for zone_name, zone in ZONES.items():
            zone_var = tk.BooleanVar(zones_frame, value=False)
            checkbutton = ttk.Checkbutton(
                zones_frame, text=zone.name, variable=zone_var)
            checkbutton.pack(anchor='w', fill='x')
            self.zones[zone_name] = zone_var
            self.zones_buttons[zone_name] = checkbutton

    def get_input(self) -> str:
        def roll_rng1(amount: int) -> None:
            # the roll event has a limit of 200 rolls
            while True:
                if amount <= 200:
                    input_data.append(f'roll rng1 {amount}')
                    break
                amount -= 200
                input_data.append('roll rng1 200')

        initiative_equip = 'selected' in self.initiative_button.state()

        input_data = []
        if initiative_equip:
            input_data.append('equip weapon tidus 1 initiative')

        starting_encounter = int(self.starting_encounter.get())
        input_data.append(f'encounters_count total {starting_encounter}')

        forced_encounters = int(self.forced_encounters.get())
        roll_rng1(forced_encounters)
        input_data.append(f'encounters_count total +{forced_encounters}')

        random_encounters = int(self.random_encounters.get())
        roll_rng1(random_encounters * 2)
        input_data.append(f'encounters_count total +{random_encounters}')
        input_data.append(f'encounters_count random +{random_encounters}')

        simulated_encounters = int(self.simulated_encounters.get())
        roll_rng1(simulated_encounters)

        input_data.append('///')

        zones = [zone for zone, active in self.zones.items() if active.get()]
        if zones:
            for _ in range(int(self.shown_encounters.get())):
                input_data.append(f'encounter multizone {' '.join(zones)}')
        return '\n'.join(input_data)

    def set_input(self, text: str) -> None:
        return

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self.initiative_button, {'invoke'}, callback_func)
        self.shown_encounters.register_callback(callback_func)
        self.starting_encounter.register_callback(callback_func)
        self.forced_encounters.register_callback(callback_func)
        self.random_encounters.register_callback(callback_func)
        self.simulated_encounters.register_callback(callback_func)
        for button in self.zones_buttons.values():
            create_command_proxy(button, {'invoke'}, callback_func)


class TkEncountersTable(TkTracker):
    tracker_type = EncountersTable
    input_widget_type = TkEncountersTableInputWidget

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 orient: Literal['vertical', 'horizontal'] = 'horizontal',
                 ) -> None:
        super().__init__(parent, parser, configs, orient)
        self.output_widget.text.config(wrap='none')
        self.output_widget.add_h_scrollbar()
