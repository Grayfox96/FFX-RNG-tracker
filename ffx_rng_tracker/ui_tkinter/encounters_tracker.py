import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..configs import UIWidgetConfigs
from ..data.encounters import EncounterData, get_encounter_notes
from ..events.parser import EventParser
from ..ui_abstract.encounters_tracker import EncountersTracker
from .base_widgets import (ScrollableFrame, TkConfirmPopup, TkWarningPopup,
                           create_command_proxy)
from .input_widget import TkSearchBarWidget
from .output_widget import TkOutputWidget


class EncounterSlider(tk.Frame):

    def __init__(self,
                 parent,
                 label: str,
                 min: int,
                 default: int,
                 max: int,
                 variable: tk.Variable = None,
                 value=None,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        self.scale = tk.Scale(
            self, orient='horizontal', label=None, from_=min, to=max)
        self.scale.set(default)
        self.scale.pack(side='left', anchor='w')

        if value is None:
            value = label
        self.button = tk.Radiobutton(
            self, text=label, variable=variable, value=value)
        self.button.pack(side='right', anchor='se')

    def get(self) -> int:
        return self.scale.get()

    def get_name(self) -> str:
        return self.button.cget(key='text')

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self.scale, {'set'}, callback_func)
        create_command_proxy(self.button, {'invoke'}, callback_func)


class TkEncountersInputWidget(tk.Frame):

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.encounters: list[EncounterData] = []

        self.initiative_button = ttk.Checkbutton(self, text='Sentry')
        self.initiative_button.grid(row=0, column=0, sticky='w')
        self.initiative_button.state(['selected'])

        self.padding_button = ttk.Checkbutton(self, text='Padding')
        self.padding_button.grid(row=0, column=1, sticky='w')
        self.padding_button.state(['selected'])

        self.current_zone = tk.StringVar(value='Start')

        self.sliders_frame = ScrollableFrame(self)
        self.sliders_frame.grid(row=1, column=0, columnspan=3, sticky='nsew')
        self.rowconfigure(1, weight=1)

        self.sliders: dict[str, EncounterSlider] = {}

        self.start_button = tk.Radiobutton(
            self, text='Start', variable=self.current_zone, value='Start')
        self.start_button.grid(row=0, column=2, sticky='w')

    def add_slider(self, label: str, min: int, default: int, max: int) -> None:
        slider = EncounterSlider(
            self.sliders_frame, label, min, default, max, self.current_zone)
        slider.pack(anchor='w')
        self.sliders[label] = slider

    def get_input(self) -> str:
        current_zone = self.current_zone.get()
        initiative = 'selected' in self.initiative_button.state()
        initiative_equipped = False

        input_data = []
        if 'selected' not in self.padding_button.state():
            input_data.append('/nopadding')
        for encounter in self.encounters:
            if initiative and encounter.initiative:
                if not initiative_equipped:
                    input_data.append('equip weapon tidus 1 initiative')
                    initiative_equipped = True
            elif initiative_equipped:
                input_data.append('equip weapon tidus 1')
                initiative_equipped = False
            if encounter.label not in self.sliders:
                encs = encounter.default
            else:
                encs = self.sliders[encounter.label].get()
                if encs >= 0:
                    if current_zone == encounter.label:
                        input_data.append('///')
                    input_data.append(f'#     {encounter.label}:')
            if ' ' in encounter.name:
                multizone = 'multizone '
            else:
                multizone = ''
            for _ in range(encs):
                input_data.append(f'encounter {multizone}{encounter.name}')
        return '\n'.join(input_data)

    def set_input(self, text: str) -> None:
        return

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self.initiative_button, {'invoke'}, callback_func)
        create_command_proxy(self.padding_button, {'invoke'}, callback_func)
        create_command_proxy(self.start_button, {'invoke'}, callback_func)
        for slider in self.sliders.values():
            slider.register_callback(callback_func)


class TkEncountersTracker(tk.Frame):

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

        input_widget = TkEncountersInputWidget(frame)
        encounters = get_encounter_notes(
            EncountersTracker.notes_file, parser.gamestate.seed)
        input_widget.encounters = encounters
        for encounter in encounters:
            if encounter.min == encounter.max:
                continue
            input_widget.add_slider(
                encounter.label, encounter.min,
                encounter.default, encounter.max)
        input_widget.pack(expand=True, fill='y')

        output_widget = TkOutputWidget(self, wrap='none')
        output_widget.pack(expand=True, fill='both', side='right')
        output_widget.text.bind(
            '<Control-s>', lambda _: self.tracker.save_input_data())

        self.tracker = EncountersTracker(
            configs=configs,
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            search_bar=search_bar,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            )
        self.tracker.callback()
