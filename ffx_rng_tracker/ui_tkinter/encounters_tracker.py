import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from itertools import count
from tkinter import ttk
from typing import Iterator, Literal

from ..configs import UIWidgetConfigs
from ..data.encounters import EncounterData, StepsData, get_encounter_notes
from ..events.parser import EventParser
from ..ui_abstract.encounters_tracker import EncountersTracker
from .base_widgets import BetterScale, ScrollableFrame
from .tkinter_utils import create_command_proxy
from .tktracker import TkTracker


@dataclass
class EncounterSlider[T: EncounterData | StepsData]:
    data: T
    scale: BetterScale | None = None
    radiobutton: ttk.Radiobutton | None = None
    label: ttk.Label | None = None

    @property
    def value(self) -> int:
        if self.scale is not None:
            return self.scale.get_input()
        return self.data.default

    @property
    def name(self) -> str:
        return self.data.label

    @property
    def zone_index(self) -> str:
        if self.radiobutton is not None:
            return f'{self.radiobutton.cget('value')}'
        return ''

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        if self.scale is not None:
            self.scale.register_callback(callback_func)
        if self.radiobutton is not None:
            create_command_proxy(self.radiobutton, {'invoke'}, callback_func)


class EncounterSliders[T: EncounterData | StepsData](ScrollableFrame):
    def __init__(self, parent: tk.Widget, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.callback_func: Callable[[], None] = lambda: None
        self.current_zone = tk.StringVar(value='Start')
        self._sliders: list[EncounterSlider[T]] = []
        self._count = count()

    def __iter__(self) -> Iterator[EncounterSlider[T]]:
        return iter(self._sliders)

    def reset(self) -> None:
        for slider in self._sliders:
            if slider.scale is not None:
                slider.scale.destroy()
                slider.scale.tk.deletecommand(str(slider.scale))
            if slider.radiobutton is not None:
                slider.radiobutton.destroy()
                slider.radiobutton.tk.deletecommand(str(slider.radiobutton))
            if slider.label is not None:
                slider.label.destroy()
        self._sliders.clear()
        self._count = count()

    def add_slider(self, data: T) -> None:
        if data.min == data.max:
            self._sliders.append(EncounterSlider(data))
            return
        row = next(self._count)
        scale = BetterScale(
            self, orient='horizontal', label=None, from_=data.min, to=data.max,
            value=data.default,
            command=lambda _: label.configure(text=slider.value))
        scale.grid(column=0, row=row, sticky='w')
        label = ttk.Label(self, text=data.default)
        label.grid(column=1, row=row, sticky='w')

        radiobutton = ttk.Radiobutton(
            self, text=data.label, variable=self.current_zone, value=row)
        radiobutton.grid(column=2, row=row, sticky='w')
        slider = EncounterSlider(data, scale, radiobutton, label)
        slider.register_callback(self.callback_func)
        self._sliders.append(slider)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        for slider in self:
            slider.register_callback(callback_func)
        self.callback_func = callback_func


class TkEncountersInputWidget(ttk.Frame):

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.initiative_button = ttk.Checkbutton(self, text='Sentry')
        self.initiative_button.grid(row=0, column=0, sticky='w')
        self.initiative_button.invoke()

        self.padding_button = ttk.Checkbutton(self, text='Padding')
        self.padding_button.grid(row=0, column=1, sticky='w')
        self.padding_button.invoke()

        self.sliders: EncounterSliders[EncounterData] = EncounterSliders(self)
        self.sliders.grid(row=1, column=0, columnspan=3, sticky='nsew')
        self.rowconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)

        self.start_button = ttk.Radiobutton(
            self, text='Start', variable=self.sliders.current_zone,
            value='Start')
        self.start_button.grid(row=0, column=2, sticky='w')

    def get_input(self) -> str:
        current_zone = self.sliders.current_zone.get()
        initiative = 'selected' in self.initiative_button.state()
        initiative_equipped = False

        input_data = []
        if 'selected' not in self.padding_button.state():
            input_data.append('/nopadding')
        for slider in self.sliders:
            if initiative and slider.data.initiative:
                if not initiative_equipped:
                    input_data.append('equip weapon tidus 1 initiative')
                    initiative_equipped = True
            elif initiative_equipped:
                input_data.append('equip weapon tidus 1')
                initiative_equipped = False
            if slider.radiobutton is not None:
                if current_zone == slider.zone_index:
                    input_data.append('///')
                input_data.append(f'#     {slider.data.label}:')
            if slider.data.name.startswith('arena '):
                line = f'encounter {slider.data.name}'
            elif ' ' in slider.data.name:
                line = f'encounter multizone {slider.data.name}'
            else:
                line = f'encounter {slider.data.name}'
            for _ in range(slider.value):
                input_data.append(line)
        return '\n'.join(input_data)

    def set_input(self, text: str) -> None:
        return

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self.initiative_button, {'invoke'}, callback_func)
        create_command_proxy(self.padding_button, {'invoke'}, callback_func)
        create_command_proxy(self.start_button, {'invoke'}, callback_func)
        self.sliders.register_callback(callback_func)


class TkEncountersTracker(TkTracker):
    tracker_type = EncountersTracker
    input_widget_type = TkEncountersInputWidget

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 orient: Literal['vertical', 'horizontal'] = 'horizontal',
                 ) -> None:
        super().__init__(parent, parser, configs, orient)
        self.input_widget: TkEncountersInputWidget
        self.output_widget.text.config(wrap='none')
        self.output_widget.add_h_scrollbar()
        encounters = get_encounter_notes(
            self.tracker.notes_file, parser.gamestate.seed)
        for encounter in encounters:
            self.input_widget.sliders.add_slider(encounter)

    def change_seed(self, seed: int, reload_notes: bool) -> None:
        if reload_notes:
            self.input_widget.sliders.reset()
            encounters = get_encounter_notes(self.tracker.notes_file, seed)
            for encounter in encounters:
                self.input_widget.sliders.add_slider(encounter)
        return super().change_seed(seed, reload_notes)
