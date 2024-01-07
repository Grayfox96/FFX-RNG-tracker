import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..data.encounter_formations import ZONES
from ..events.parser import EventParser
from ..ui_abstract.encounters_planner import EncountersPlanner
from ..utils import stringify
from .base_widgets import ScrollableFrame, TkConfirmPopup, TkWarningPopup
from .encounters_tracker import EncounterSlider, TkEncountersOutputWidget
from .input_widget import TkSearchBarWidget


class TkEncountersPlannerInputWidget(tk.Frame):

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.callback_func: Callable = None

        self.searchbar = TkSearchBarWidget(self)
        self.searchbar.pack(fill='x')
        self.searchbar.set_input('Type monster names here')

        options = ['Boss', 'Simulation']
        options.extend([z.name for z in ZONES.values()])
        self.selected_zone = tk.StringVar(self)
        self.selected_zone.set(options[0])
        combobox = ttk.Combobox(
            self, values=options, state='readonly',
            textvariable=self.selected_zone)
        combobox.pack(fill='x')
        button = tk.Button(
            self, text='Add Slider',
            command=lambda: self.add_slider(self.selected_zone.get()))
        button.pack(fill='x')

        self.initiative_button = ttk.Checkbutton(self, text='Initiative')
        self.initiative_button.pack(fill='x')
        self.initiative_button.state(['selected'])

        self.current_zone_index = tk.IntVar(self, value=0)

        self.sliders_frame = ScrollableFrame(self)
        self.sliders_frame.pack(expand=True, fill='both')
        self.sliders: list[EncounterSlider] = []

    def add_slider(self,
                   label: str,
                   min: int = 0,
                   default: int = 1,
                   max: int = 100
                   ) -> None:
        value = len(self.sliders)
        slider = EncounterSlider(
            self.sliders_frame, label, min, default, max,
            self.current_zone_index, value, self.callback_func)
        slider.pack(anchor='w')
        self.sliders.append(slider)

    def get_input(self) -> str:
        current_zone_index = self.current_zone_index.get()
        initiative_equip = 'selected' in self.initiative_button.state()
        input_data = []
        if initiative_equip:
            input_data.append('equip weapon tidus 1 initiative')
        for index, scale in enumerate(self.sliders):
            name = (stringify(scale.get_name())
                    .replace('(', '')
                    .replace(')', '')
                    .replace('-', '_')
                    .replace('\'', '')
                    )
            while '__' in name:
                name = name.replace('__', '_')
            match name:
                case 'boss':
                    name = 'dummy'
                case 'simulation':
                    name = 'simulation'
            for count in range(scale.get()):
                if count == 0:
                    if index == current_zone_index:
                        input_data.append('///')
                    if name in ZONES:
                        input_data.append(f'#     {ZONES[name].name}:')
                line = f'encounter {name}'
                input_data.append(line)
        return '\n'.join(input_data)

    def set_input(self, text: str) -> None:
        return

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        self.searchbar.register_callback(callback_func)
        self.initiative_button.config(command=callback_func)
        for slider in self.sliders:
            slider.config(command=callback_func)
        self.callback_func = callback_func


class TkEncountersPlanner(tk.Frame):
    """"""

    def __init__(self, parent, parser: EventParser, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        input_widget = TkEncountersPlannerInputWidget(self)
        input_widget.pack(fill='y', side='left')

        output_widget = TkEncountersOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = EncountersPlanner(
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            search_bar=input_widget.searchbar,
            )
