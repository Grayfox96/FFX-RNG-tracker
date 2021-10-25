import tkinter as tk
from tkinter import ttk
from typing import Union

from ..data.encounters import ANY_ENCOUNTERS
from ..data.file_functions import get_sliders_settings
from ..events import (Comment, Encounter, MultizoneRandomEncounter,
                      RandomEncounter, SimulatedEncounter)
from .base_widgets import (BaseWidget, BetterSpinbox, BetterText,
                           ScrollableFrame)


class EncountersTracker(BaseWidget):
    """Widget used to track encounters RNG."""

    def __init__(self, parent, *args, **kwargs) -> None:
        self.sliders_settings = get_sliders_settings(
            'data/encounters_settings.csv')
        super().__init__(parent, *args, **kwargs)

    def make_input_widget(
            self) -> dict[str, Union[ttk.Checkbutton, tk.StringVar, dict[str, tk.Scale]]]:
        outer_frame = tk.Frame(self)
        outer_frame.pack(fill='y', side='left')
        frame = ScrollableFrame(outer_frame)
        frame.pack(expand=True, fill='both')
        sentry = ttk.Checkbutton(
            frame, text='Sentry', command=self.print_output)
        sentry.grid(row=0, column=0, sticky='nsew')
        sentry.state(['selected'])
        current_zone = tk.StringVar(value='Start')
        start = tk.Radiobutton(
            frame, text='Start', variable=current_zone,
            value='Start', command=self.print_output)
        start.grid(row=0, column=1, sticky='sw')
        widget = {
            'sentry': sentry,
            'current_zone': current_zone,
            'zones': {},
        }
        for row, (zone, settings) in enumerate(self.sliders_settings.items()):
            row += 1
            scale = tk.Scale(
                frame, orient='horizontal', label=None,
                from_=settings['min'], to=settings['max'],
                command=lambda _: self.print_output())
            scale.set(settings['default'])
            scale.grid(row=row, column=0)
            label = tk.Radiobutton(
                frame, text=zone, variable=current_zone,
                value=zone, command=self.print_output)
            label.grid(row=row, column=1, sticky='sw')
            widget['zones'][zone] = scale
        return widget

    def get_input(self) -> None:
        self.rng_tracker.reset()
        # if the sentry checkbutton is either selected or indeterminate
        # set sentry to true
        sentry = self.input_widget['sentry'].state()
        sentry = 'selected' in sentry or 'alternate' in sentry

        for encounter in ANY_ENCOUNTERS:
            encounter_type = encounter['enc_type']
            name = encounter['name']
            if sentry:
                initiative = encounter['initiative']
            else:
                initiative = False
            forced_condition = encounter['forced_condition']
            if encounter_type == 'random':
                for _ in range(self.input_widget['zones'][name].get()):
                    self.rng_tracker.events_sequence.append(
                        RandomEncounter(name, initiative, forced_condition))
            elif encounter_type == 'set':
                self.rng_tracker.events_sequence.append(
                    Encounter(name, initiative, forced_condition))
            elif encounter_type == 'set_optional':
                for _ in range(self.input_widget['zones'][name].get()):
                    self.rng_tracker.events_sequence.append(
                        Encounter(name, initiative, forced_condition))
            elif encounter_type == 'simulated':
                for _ in range(self.input_widget['zones'][name].get()):
                    self.rng_tracker.events_sequence.append(
                        SimulatedEncounter(name, initiative, forced_condition))
            elif encounter_type == 'multizone':
                zones = name.split('/')
                for _ in range(self.input_widget['zones'][name].get()):
                    self.rng_tracker.events_sequence.append(
                        MultizoneRandomEncounter(
                            zones, initiative, forced_condition))

    def print_output(self) -> None:
        self.get_input()
        data = []
        for event in self.rng_tracker.events_sequence:
            line = str(event)[10:]
            # add a separator between zones
            if '[1]' in line:
                data.append('=' * 50)
            data.append(line)
        data = '\n'.join(data)
        index = data.find(self.input_widget['current_zone'].get())
        if index > 0:
            data = data[index - 5:]

        self.output_widget.config(state='normal')
        self.output_widget.set(data)
        self.output_widget.highlight_pattern('Preemptive', 'green')
        self.output_widget.highlight_pattern('Ambush', 'red')
        for enemy in ('Bomb', 'Basilisk', 'Funguar', 'Iron Giant', 'Ghost'):
            self.output_widget.highlight_pattern(enemy, 'highlight')
        self.output_widget.highlight_pattern(
            '^.+$', 'wrap_margin', regexp=True)
        self.output_widget.config(state='disabled')
