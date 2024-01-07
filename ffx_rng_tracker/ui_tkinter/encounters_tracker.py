import re
import tkinter as tk
from tkinter import ttk
from typing import Callable

from ..configs import Configs
from ..data.encounters import EncounterData, get_encounter_notes
from ..events.parser import EventParser
from ..ui_abstract.encounters_tracker import EncountersTracker
from .base_widgets import ScrollableFrame, TkConfirmPopup, TkWarningPopup
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
                 command: Callable = None,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        self.scale = tk.Scale(
            self, orient='horizontal', label=None, from_=min, to=max,
            command=command)
        self.scale.set(default)
        self.scale.pack(side='left', anchor='w')

        if value is None:
            value = label
        self.button = tk.Radiobutton(
            self, text=label, variable=variable, value=value, command=command)
        self.button.pack(side='right', anchor='se')

    def get(self) -> int:
        return self.scale.get()

    def get_name(self) -> str:
        return self.button.cget(key='text')

    def config(self, command=None, *args, **kwargs) -> None:
        if command is not None:
            self.scale.config(command=command)
            self.button.config(command=command)
        super().config(*args, **kwargs)


class TkEncountersInputWidget(tk.Frame):

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.encounters: list[EncounterData] = []

        self.callback_func: Callable = None

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
        self.initiative_button.config(command=callback_func)
        self.padding_button.config(command=callback_func)
        self.start_button.config(command=callback_func)
        for slider in self.sliders.values():
            slider.config(command=callback_func)
        self.callback_func = callback_func


class TkEncountersOutputWidget(TkOutputWidget):

    def __init__(self, parent, *args, **kwargs) -> None:
        kwargs.setdefault('wrap', 'none')
        super().__init__(parent, *args, **kwargs)

    def get_regex_patterns(self) -> dict[str, str]:
        important_monsters = '(?i)' + '|'.join(
            [re.escape(m) for m in Configs.important_monsters])
        patterns = {
            'preemptive': r'\mPreemptive\M',
            'ambush': r'\mAmbush\M',
            'important monster': important_monsters,
            'encounter': '^# (=| ).+$',
            'error': '^# Error: .+$',
        }
        return patterns


class TkEncountersTracker(tk.Frame):

    def __init__(self, parent, parser: EventParser, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        input_widget = TkEncountersInputWidget(self)
        encounters = get_encounter_notes(
            EncountersTracker.notes_file, parser.gamestate.seed)
        input_widget.encounters = encounters
        for encounter in encounters:
            if encounter.min == encounter.max:
                continue
            input_widget.add_slider(
                encounter.label, encounter.min,
                encounter.default, encounter.max)
        input_widget.pack(fill='y', side='left')

        output_widget = TkEncountersOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')
        output_widget.bind(
            '<Control-s>', lambda _: self.tracker.save_input_data())

        self.tracker = EncountersTracker(
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            )
