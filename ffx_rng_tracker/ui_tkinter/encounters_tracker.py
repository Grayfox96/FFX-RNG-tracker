import tkinter as tk
from tkinter import ttk
from typing import Union

from ..data.encounters import ANY_ENCOUNTERS
from ..ui_functions import parse_encounter
from .base_widgets import BaseWidget, ScrollableFrame


class EncountersTracker(BaseWidget):
    """Widget used to track encounters RNG."""

    def make_input_widget(
            self) -> dict[str, Union[ttk.Checkbutton, tk.StringVar, dict[str, tk.Scale]]]:
        outer_frame = tk.Frame(self)
        outer_frame.pack(fill='y', side='left')
        outer_frame.rowconfigure(index=1, weight=1)
        sentry = ttk.Checkbutton(
            outer_frame, text='Sentry', command=self.print_output)
        sentry.grid(row=0, column=0, sticky='w')
        sentry.state(['selected'])
        current_zone = tk.StringVar(value='Start')
        frame = ScrollableFrame(outer_frame)
        frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
        start = tk.Radiobutton(
            frame, text='Start', variable=current_zone,
            value='Start', command=self.print_output)
        start.grid(row=0, column=1, sticky='w')
        widget = {
            'sentry': sentry,
            'current_zone': current_zone,
            'scales': {},
        }
        for row, encounter in enumerate(ANY_ENCOUNTERS):
            if not encounter['label']:
                continue
            row += 1
            scale = tk.Scale(
                frame, orient='horizontal', label=None,
                from_=encounter['min'], to=encounter['max'],
                command=lambda _: self.print_output())
            scale.set(encounter['default'])
            scale.grid(row=row, column=0)
            label = tk.Radiobutton(
                frame, text=encounter['label'], variable=current_zone,
                value=encounter['label'], command=self.print_output)
            label.grid(row=row, column=1, sticky='sw')
            widget['scales'][encounter['label']] = scale
        return widget

    def get_input(self) -> None:
        self.rng_tracker.reset()
        # if the sentry checkbutton is either selected or indeterminate
        # set sentry to true
        sentry = self.input_widget['sentry'].state()
        sentry = 'selected' in sentry or 'alternate' in sentry

        for encounter in ANY_ENCOUNTERS:
            if sentry:
                initiative = encounter['initiative']
            else:
                initiative = ''
            if encounter['type'] == 'set':
                encs = 1
            else:
                encs = self.input_widget['scales'][encounter['label']].get()
            for _ in range(encs):
                event = parse_encounter(
                    encounter['type'],
                    encounter['name'],
                    initiative,
                    encounter['forced_condition'],
                    )
                self.rng_tracker.events_sequence.append(event)

    def print_output(self) -> None:
        self.get_input()
        data = []
        spacer = '=' * 60
        last_zone = ''
        for event in self.rng_tracker.events_sequence:
            line = str(event)
            if '|' in line:
                if last_zone != event.zone:
                    data.append(spacer)
                    last_zone = event.zone
                    data.append(f'     {event.name}:')
                data.append(line[10:21] + line[23 + len(event.zone):])
            else:
                last_zone = ''
                data.append(line[10:])
        data = '\n'.join(data)
        for encounter in ANY_ENCOUNTERS:
            if encounter['label'] == self.input_widget['current_zone'].get():
                current_zone = encounter['name']
                break
        else:
            current_zone = ''
        index = data.find(current_zone)
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
