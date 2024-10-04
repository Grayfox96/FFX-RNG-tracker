import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from ..configs import UIWidgetConfigs
from ..data.encounter_formations import ZONES
from ..data.encounters import EncounterData
from ..events.parser import EventParser
from ..ui_abstract.encounters_planner import EncountersPlanner
from ..utils import stringify
from .base_widgets import TkConfirmPopup, TkWarningPopup, create_command_proxy
from .encounters_tracker import EncounterSliders
from .input_widget import TkSearchBarWidget
from .output_widget import TkOutputWidget


class TkEncountersPlannerInputWidget(tk.Frame):

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        options = ['Boss', 'Simulation']
        options.extend(z.name for z in ZONES.values())
        self.selected_zone = tk.StringVar(self)
        self.selected_zone.set(options[0])
        combobox = ttk.Combobox(
            self, values=options, state='readonly',
            textvariable=self.selected_zone)
        combobox.pack(fill='x')
        self.add_slider_button = tk.Button(
            self, text='Add Slider', command=lambda: self.add_slider())
        self.add_slider_button.pack(fill='x')

        self.initiative_button = ttk.Checkbutton(self, text='Initiative')
        self.initiative_button.pack(fill='x')
        self.initiative_button.state(['selected'])

        self.sliders = EncounterSliders(self)
        self.sliders.pack(expand=True, fill='both')

    def add_slider(self) -> None:
        label = self.selected_zone.get()
        name = (stringify(label)
                .replace('-', '_')
                )
        while '__' in name:
            name = name.replace('__', '_')
        match name:
            case 'boss':
                name = 'dummy'
            case 'simulation':
                name = 'simulation'
        data = EncounterData(
            name=name,
            initiative=True,
            label=self.selected_zone.get(),
            min=0,
            default=0,
            max=100
            )
        self.sliders.add_slider(data)
        self.sliders.callback_func()

    def get_input(self) -> str:
        current_zone = self.sliders.current_zone.get()
        initiative_equip = 'selected' in self.initiative_button.state()
        input_data = []
        if initiative_equip:
            input_data.append('equip weapon tidus 1 initiative')
        for slider in self.sliders:
            if current_zone == slider.zone_index:
                input_data.append('///')
            input_data.append(f'#     {slider.data.label}:')
            for _ in range(slider.value):
                line = f'encounter {slider.data.name}'
                input_data.append(line)
        return '\n'.join(input_data)

    def set_input(self, text: str) -> None:
        return

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self.initiative_button, {'invoke'}, callback_func)
        create_command_proxy(self.add_slider_button, {'invoke'}, callback_func)
        self.sliders.register_callback(callback_func)


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
