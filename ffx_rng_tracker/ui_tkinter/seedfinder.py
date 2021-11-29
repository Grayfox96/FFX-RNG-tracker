import sys
import tkinter as tk
from tkinter import messagebox

from ..data.seeds import (DAMAGE_VALUES_NEEDED, HD_FROM_BOOT_FRAMES,
                          PS2_FROM_BOOT_FRAMES, datetime_to_seed)
from ..events import CharacterAction
from ..main import get_tracker
from .actions_tracker import ActionsTracker
from .base_widgets import BetterText


class SeedFinder(ActionsTracker):
    '''Widget used to find the starting seed.'''

    def make_input_widget(self) -> BetterText:
        frame = tk.Frame(self)
        frame.pack(fill='y', side='left')
        tk.Label(frame, text='Actions').pack()
        text = BetterText(
            frame, font=self.font, width=40, undo=True, autoseparators=True,
            maxundo=-1)
        text.set('encounter\n'
                 'auron attack sinscale\ntidus attack sinscale\n'
                 'auron attack sinscale\ntidus attack sinscale\n'
                 'auron attack sinscale\ntidus attack sinscale\n')
        text.pack(fill='y', expand=True)
        text.bind('<KeyRelease>', lambda _: self.print_output())
        text.damage_input = tk.StringVar(frame)
        tk.Label(frame, text='Damage values').pack()
        tk.Entry(frame, textvariable=text.damage_input).pack(fill='x')
        tk.Button(frame, text='Search Seed', command=self.find_seed).pack()
        return text

    def find_seed(self) -> None:
        if '-ps2' in sys.argv:
            frames = PS2_FROM_BOOT_FRAMES
        else:
            frames = HD_FROM_BOOT_FRAMES
        indexes = []
        for index, event in enumerate(self.rng_tracker.events_sequence):
            if isinstance(event, CharacterAction):
                if event.action.does_damage:
                    indexes.append(index)
        if len(indexes) < DAMAGE_VALUES_NEEDED:
            messagebox.showwarning(
                message=f'Need {DAMAGE_VALUES_NEEDED} damaging actions.')
            return
        input_dvs = self.input_widget.damage_input.get()
        for symbol in (',', '-', '/', '\\', '.'):
            input_dvs = input_dvs.replace(symbol, ' ')
        input_dvs = input_dvs.split()
        try:
            input_dvs = [int(i) for i in input_dvs]
        except ValueError as error:
            error = str(error).split(':', 1)[1]
            messagebox.showwarning(
                message=f'{error} is not a valid damage value.')
            return
        if len(input_dvs) < len(indexes):
            messagebox.showwarning(
                message=f'Need {len(indexes)} damage values.')
            return
        input_dvs = input_dvs[:len(indexes)]

        rng_tracker = get_tracker()
        damage_values = []
        for frame in range(frames):
            for dt in range(256):
                seed = datetime_to_seed(dt, frame)
                rng_tracker.__init__(seed)
                self.get_input()
                damage_values.clear()
                for index in indexes:
                    event = self.rng_tracker.events_sequence[index]
                    damage_values.append(event.damage)
                if damage_values == input_dvs:
                    self.input_widget.insert('1.0', f'# Seed number: {seed}\n')
                    self.print_output()
                    messagebox.showinfo(message=f'Seed number: {seed}')
                    return
        else:
            messagebox.showwarning(message='Seed not found!')
