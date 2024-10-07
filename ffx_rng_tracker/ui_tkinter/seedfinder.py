import tkinter as tk
from tkinter import ttk

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_abstract.seedfinder import SeedFinder
from .base_widgets import TkConfirmPopup, TkWarningPopup
from .input_widget import TkInputWidget, TkSearchBarWidget
from .output_widget import TkOutputWidget


class TkSeedFinderInputWidget(TkInputWidget):
    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.damage_values = tk.StringVar(self)

    def get_input(self) -> str:
        text = (f'{self.damage_values.get()}\n'
                f'///\n'
                f'{super().get_input()}'
                )
        return text


class TkSeedFinder(ttk.Frame):
    """Widget used to find the starting seed."""

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        frame = ttk.Frame(self)
        frame.pack(fill='y', side='left')

        search_bar = TkSearchBarWidget(frame)
        search_bar.pack(fill='x')

        ttk.Label(frame, text='Actions').pack()

        input_widget = TkSeedFinderInputWidget(frame)
        input_widget.pack(expand=True, fill='y')

        ttk.Label(frame, text='Damage values').pack()

        ttk.Entry(frame, textvariable=input_widget.damage_values).pack(fill='x')

        button = ttk.Button(frame, text='Search Seed')
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
        )
        button.configure(command=self.tracker.find_seed)
        self.tracker.callback()
