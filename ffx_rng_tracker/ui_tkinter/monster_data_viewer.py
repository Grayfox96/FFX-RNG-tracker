import tkinter as tk
from tkinter import font

from ..data.monsters import MONSTERS
from ..ui_functions import format_monster_data
from .base_widgets import BaseWidget, BetterText


class MonsterDataViewer(BaseWidget):
    """Widget used to display monster's data."""

    def __init__(self, parent, *args, **kwargs):
        self.monsters_names = sorted(list(MONSTERS.keys()))
        self.monsters_data = {k: format_monster_data(v)
                              for k, v in MONSTERS.items()}
        self.parent = parent
        self.font = font.Font(family='Courier New', size=9)
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.input_widget = self.make_input_widget()
        self.output_widget = self.make_output_widget()
        self.print_output()

    def make_input_widget(self) -> tk.Listbox:
        frame = tk.Frame(self)
        frame.pack(fill='y', side='left')
        inner_frame = tk.Frame(frame)
        inner_frame.pack(fill='x')
        tk.Label(inner_frame, text='Search:').pack(side='left')
        entry = tk.Entry(inner_frame)
        entry.bind('<KeyRelease>', lambda _: self.filter_monsters())
        entry.pack(fill='x', side='right')
        listvar = tk.StringVar(value=self.monsters_names)
        listbox = tk.Listbox(frame, width=30, listvariable=listvar)
        listbox.bind('<<ListboxSelect>>', lambda _: self.print_output())
        listbox.pack(expand=True, fill='y')
        listbox.listvar = listvar
        listbox.entry = entry
        return listbox

    def make_output_widget(self) -> BetterText:
        widget = super().make_output_widget()
        widget.configure(wrap='none')
        widget._add_h_scrollbar()
        return widget

    def get_input(self) -> tuple[int]:
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
            monster_data = self.monsters_data[monster_name]
        except KeyError:
            return
        self.output_widget.config(state='normal')
        self.output_widget.set(monster_data)
        self.output_widget.config(state='disabled')

    def filter_monsters(self) -> None:
        input = self.input_widget.entry.get().lower()
        self.monsters_names = [name
                               for name, data in self.monsters_data.items()
                               if input in name or input in data.lower()]
        self.monsters_names.sort()
        self.input_widget.listvar.set(self.monsters_names)
