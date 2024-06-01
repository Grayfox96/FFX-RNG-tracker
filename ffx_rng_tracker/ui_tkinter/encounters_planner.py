import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from ..configs import UIWidgetConfigs
from ..data.encounter_formations import ZONES
from ..events.parser import EventParser
from ..ui_abstract.encounters_planner import EncountersPlanner
from ..utils import stringify
from .base_widgets import (ScrollableFrame, TkConfirmPopup, TkWarningPopup,
                           create_command_proxy)
from .encounters_tracker import EncounterSlider
from .input_widget import TkSearchBarWidget
from .output_widget import TkOutputWidget


class TkEncountersPlannerInputWidget(tk.Frame):

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.callback_func: Callable[[], None] = lambda: None

        options = ['Boss', 'Simulation']
        options.extend(z.name for z in ZONES.values())
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

    def add_slider(self, label: str) -> None:
        value = len(self.sliders)
        slider = EncounterSlider(
            parent=self.sliders_frame,
            label=label,
            min=0,
            default=0,
            max=100,
            variable=self.current_zone_index,
            value=value,
            )
        slider.register_callback(self.callback_func)
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
        create_command_proxy(self.initiative_button, {'invoke'}, callback_func)
        for slider in self.sliders:
            slider.register_callback(callback_func)
        self.callback_func = callback_func


class TkEncountersPlanner(tk.Frame):
    """"""

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)
        frame = tk.Frame(self)
        frame.pack(fill='y', side='left')

        search_bar = TkSearchBarWidget(frame)
        search_bar.pack(fill='x')

        input_widget = TkEncountersPlannerInputWidget(frame)
        input_widget.pack(expand=True, fill='y')

        output_widget = TkOutputWidget(self, wrap='none')
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = EncountersPlanner(
            configs=configs,
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            search_bar=search_bar,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            )
