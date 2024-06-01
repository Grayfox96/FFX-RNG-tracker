import tkinter as tk
from collections.abc import Callable

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_abstract.seedfinder import SeedFinder
from .base_widgets import TkConfirmPopup, TkWarningPopup
from .input_widget import TkInputWidget, TkSearchBarWidget
from .output_widget import TkOutputWidget


class TkDamageValuesWidget(tk.StringVar):

    def get_input(self) -> str:
        return self.get()

    def set_input(self, text: str) -> None:
        self.set(text)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        raise NotImplementedError()


class TkSeedFinder(tk.Frame):
    """Widget used to find the starting seed."""

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

        tk.Label(frame, text='Actions').pack()

        input_widget = TkInputWidget(frame)
        input_widget.pack(expand=True, fill='y')

        tk.Label(frame, text='Damage values').pack()

        damage_values_widget = TkDamageValuesWidget(self)
        tk.Entry(frame, textvariable=damage_values_widget).pack(fill='x')

        button = tk.Button(frame, text='Search Seed')
        button.pack()

        output_widget = TkOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = SeedFinder(
            configs=configs,
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            search_bar=search_bar,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            damage_values_widget=damage_values_widget,
        )
        button.configure(command=self.tracker.find_seed)
        self.tracker.callback()
