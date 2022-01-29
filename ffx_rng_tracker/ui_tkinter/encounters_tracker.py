import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

from ..configs import Configs
from ..data.encounters import ANY_ENCOUNTERS
from ..ui_functions import parse_encounter
from .base_widgets import BaseWidget, ScrollableFrame


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
            outer_frame, text='Sentry', command=self.print_output)
        initiative_equip.grid(row=0, column=0, sticky='w')
        initiative_equip.state(['selected'])
        current_zone = tk.StringVar(value='Start')
        frame = ScrollableFrame(outer_frame)
        frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
        start = tk.Radiobutton(
            frame, text='Start', variable=current_zone,
            value='Start', command=self.print_output)
        start.grid(row=0, column=1, sticky='w')
        scales = {}
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
            scales[encounter['label']] = scale
        widget = EncountersTrackerInputWidget(
            initiative_equip=initiative_equip,
            current_zone=current_zone,
            scales=scales,
            )
        return widget

    def set_tags(self) -> list[tuple[str, str, bool]]:
        important_monsters = '(?i)' + '|'.join(Configs.important_monsters)
        tags = [
            ('Preemptive', 'preemptive', False),
            ('Ambush', 'ambush', False),
            (important_monsters, 'important monster', True),
        ]
        tags.extend(super().set_tags())
        return tags

    def get_input(self) -> None:
        self.rng_tracker.reset()
        # if the initiative checkbutton is either selected or indeterminate
        # set initiative to true
        initiative_equip = self.input_widget.initiative_equip.state()
        initiative_equip = 'selected' in initiative_equip

        for encounter in ANY_ENCOUNTERS:
            if initiative_equip:
                initiative = encounter['initiative']
            else:
                initiative = ''
            if encounter['type'] == 'set':
                encs = 1
            else:
                encs = self.input_widget.scales[encounter['label']].get()
            for _ in range(encs):
                event = parse_encounter(
                    encounter_type=encounter['type'],
                    name=encounter['name'],
                    initiative=initiative,
                    forced_condition=encounter['forced_condition'],
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
        current_zone = self.input_widget.current_zone.get()
        for encounter in ANY_ENCOUNTERS:
            if encounter['label'] == current_zone:
                current_zone = encounter['name']
                break
        else:
            current_zone = ''
        index = data.find(current_zone)
        if index > 0:
            data = data[index - 5:]

        self.output_widget.config(state='normal')
        self.output_widget.set(data)
        self.highlight_patterns()
        self.output_widget.config(state='disabled')
        self.output_widget.highlight_pattern(
            '^.+$', 'wrap_margin', regexp=True)
        self.output_widget.config(state='disabled')
