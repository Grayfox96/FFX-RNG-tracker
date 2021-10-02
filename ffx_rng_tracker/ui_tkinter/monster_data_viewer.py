import tkinter as tk
from tkinter import font

from ..data.monsters import MONSTERS
from ..ui_functions import format_monster_data
from .base_widgets import BaseWidget, BetterText


class MonsterDataViewer(BaseWidget):
    """Widget used to display monster's data."""

    def __init__(self, parent, *args, **kwargs):
        self.monsters_names = sorted(list(MONSTERS.keys()))
        self.parent = parent
        self.font = font.Font(family='Courier New', size=9)
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.input_widget = self.make_input_widget()
        self.output_widget = self.make_output_widget()
        self.print_output()

    def make_input_widget(self) -> tk.Listbox:
        listvar = tk.StringVar(value=self.monsters_names)
        listbox = tk.Listbox(self, width=30, listvariable=listvar)
        listbox.bind('<<ListboxSelect>>', lambda _: self.print_output())
        listbox.pack(fill='y', side='left')
        return listbox

    def make_output_widget(self) -> BetterText:
        widget = super().make_output_widget()
        widget.configure(wrap='none')
        return widget

    def get_input(self) -> str:
        return self.input_widget.curselection()

    def print_output(self) -> None:
        input = self.get_input()
        try:
            monster_index = input[0]
        # deselecting triggers the bind
        # giving an empty string as the index
        except IndexError:
            return
        monster_name = self.monsters_names[monster_index]
        try:
            monster = MONSTERS[monster_name]
        except KeyError:
            return
        monster_data = format_monster_data(monster)
        self.output_widget.config(state='normal')
        self.output_widget.set(monster_data)
        self.output_widget.config(state='disabled')
