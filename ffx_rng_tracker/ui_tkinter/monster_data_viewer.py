import tkinter as tk
from dataclasses import dataclass

from ..data.monsters import MONSTERS
from ..ui_functions import format_monster_data
from .base_widgets import BaseWidget, ScrollableText


@dataclass
class MonsterDataViewerInputWidget:
    listbox: tk.Listbox
    listvar: tk.StringVar
    entry: tk.Entry


class MonsterDataViewer(BaseWidget):
    """Widget used to display monster's data."""

    def __init__(self, parent, seed: int = 0, *args, **kwargs) -> None:
        self.monsters_names = sorted(list(MONSTERS.keys()))
        self.monsters_data = {k: format_monster_data(v)
                              for k, v in MONSTERS.items()}
        super().__init__(parent, seed, *args, **kwargs)

    def make_input_widget(self) -> MonsterDataViewerInputWidget:
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
        listbox.bind('<<ListboxSelect>>', lambda _: self.parse_input())
        listbox.pack(expand=True, fill='y')
        widget = MonsterDataViewerInputWidget(
            listbox=listbox,
            listvar=listvar,
            entry=entry,
        )
        return widget

    def make_output_widget(self) -> ScrollableText:
        widget = super().make_output_widget()
        widget.configure(wrap='none')
        widget._add_h_scrollbar()
        return widget

    def get_tags(self) -> dict[str, str]:
        return {}

    def get_default_input_text(self) -> str:
        return self.get_input()

    def get_input(self) -> str:
        input_data = self.input_widget.listbox.curselection()
        try:
            monster_index = input_data[0]
        # deselecting triggers the bind
        # giving an empty string as the index
        except IndexError:
            return ''
        return self.monsters_names[monster_index]

    def parse_input(self) -> None:
        input_data = self.get_input()
        try:
            monster_data = self.monsters_data[input_data]
        except KeyError:
            return

        self.print_output(monster_data)

    def filter_monsters(self) -> None:
        input_data = self.input_widget.entry.get().lower()
        self.monsters_names = [name
                               for name, data in self.monsters_data.items()
                               if input_data in name
                               or input_data in data.lower()]
        self.monsters_names.sort()
        self.input_widget.listvar.set(self.monsters_names)
