import tkinter as tk
from typing import Callable

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_abstract.monster_data_viewer import MonsterDataViewer
from .base_widgets import create_command_proxy
from .input_widget import TkSearchBarWidget
from .output_widget import TkOutputWidget


class TkMonsterSelectionWidget(tk.Listbox):

    def __init__(self, parent, *args, **kwargs) -> None:
        kwargs.setdefault('listvariable', tk.StringVar())
        super().__init__(parent, *args, **kwargs)
        self._listvar: tk.StringVar = kwargs['listvariable']
        self._monster_names: list[str] = []

    def get_input(self) -> str:
        input_data = self.curselection()
        try:
            monster_index = input_data[0]
        # if there is nothing selected
        # curselection returns an empty tuple
        except IndexError:
            return ''
        return self._monster_names[monster_index]

    def set_input(self, data: str) -> None:
        old_selection, *monster_names = data.split('|')
        self._monster_names = monster_names
        self._listvar.set(monster_names)
        try:
            index = monster_names.index(old_selection)
        except ValueError:
            index = 0
        self.selection_clear(0, 'end')
        self.selection_set(index)
        self.activate(index)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self, {'activate'}, callback_func)


class TkMonsterDataViewer(tk.Frame):
    """Widget used to display monster's data."""

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        frame = tk.Frame(self)
        frame.pack(fill='y', side='left')

        search_bar = TkSearchBarWidget(frame)
        search_bar.pack(fill='x')

        monster_selection_widget = TkMonsterSelectionWidget(frame, width=30)
        monster_selection_widget.pack(expand=True, fill='y')

        output_widget = TkOutputWidget(self, wrap='none')
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = MonsterDataViewer(
            configs=configs,
            monster_selection_widget=monster_selection_widget,
            search_bar=search_bar,
            output_widget=output_widget,
        )
