import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk

from ..configs import Configs
from ..data.encounters import ANY_ENCOUNTERS
from ..events.comment import Comment
from ..events.encounter import (Encounter, MultizoneRandomEncounter,
                                RandomEncounter)
from ..events.parsing import parse_encounter
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
            outer_frame, text='Sentry', command=self.parse_input)
        initiative_equip.grid(row=0, column=0, sticky='w')
        initiative_equip.state(['selected'])
        current_zone = tk.StringVar(value='Start')
        frame = ScrollableFrame(outer_frame)
        frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
        start = tk.Radiobutton(
            frame, text='Start', variable=current_zone,
            value='Start', command=self.parse_input)
        start.grid(row=0, column=1, sticky='w')
        scales = {}
        for row, encounter in enumerate(ANY_ENCOUNTERS, start=1):
            if encounter['type'] == 'set':
                continue
            scale = tk.Scale(
                frame, orient='horizontal', label=None,
                from_=encounter['min'], to=encounter['max'],
                command=lambda _: self.parse_input())
            scale.set(encounter['default'])
            scale.grid(row=row, column=0)
            label = tk.Radiobutton(
                frame, text=encounter['label'], variable=current_zone,
                value=encounter['label'], command=self.parse_input)
            label.grid(row=row, column=1, sticky='sw')
            scales[encounter['label']] = scale
        widget = EncountersTrackerInputWidget(
            initiative_equip=initiative_equip,
            current_zone=current_zone,
            scales=scales,
            )
        return widget

    def get_tags(self) -> list[tuple[str, str, bool]]:
        important_monsters = '(?i)' + '|'.join(Configs.important_monsters)
        tags = [
            ('^.+$', 'wrap_margin', True),
            ('Preemptive', 'preemptive', False),
            ('Ambush', 'ambush', False),
            (important_monsters, 'important monster', True),
        ]
        return tags

    def get_default_input_text(self) -> str:
        return self.get_input()

    def get_input(self) -> str:
        initiative_equip = self.input_widget.initiative_equip.state()
        initiative_equip = 'selected' in initiative_equip

        spacer = '=' * 60
        input_data = []
        for encounter in ANY_ENCOUNTERS:
            if initiative_equip:
                initiative = encounter['initiative']
            else:
                initiative = 'false'
            if encounter['type'] == 'set':
                encs = 1
            else:
                encs = self.input_widget.scales[encounter['label']].get()
                if encs > 0:
                    input_data.append(spacer)
                    input_data.append(f'     {encounter["label"]}:')
            for _ in range(encs):
                event = ' '.join([
                    'encounter',
                    encounter['type'],
                    encounter['name'],
                    initiative,
                    encounter['forced_condition'],
                ])
                input_data.append(event)
        return '\n'.join(input_data)

    def parse_input(self) -> None:
        input_data = self.get_input()
        input_lines = input_data.split('\n')

        gs = self.gamestate
        gs.reset()

        # parse through the input text
        for line in input_lines:
            match line.split():
                case ['encounter', *params]:
                    event = parse_encounter(gs, *params)
                case _:
                    event = Comment(gs, line)

            self.gamestate.events_sequence.append(event)

        output_data = []
        for event in self.gamestate.events_sequence:
            match event:
                case RandomEncounter():
                    string = str(event)
                    output_data.append(
                        string[10:21] + string[23 + len(event.zone):])
                case MultizoneRandomEncounter():
                    zones = '/'.join(event.zones)
                    string = str(event)
                    output_data.append(
                        string[10:21] + string[23 + len(zones):])
                case Encounter():
                    output_data.append(str(event)[10:])
                case _:
                    output_data.append(str(event))

        data = '\n'.join(output_data)
        current_zone = self.input_widget.current_zone.get()
        index = data.find(current_zone)
        if index > 0:
            data = data[index - 5:]

        self.print_output(data)
