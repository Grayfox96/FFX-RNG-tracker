import tkinter as tk
from tkinter import ttk
from typing import Literal

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_abstract.base_tracker import TrackerUI
from .base_widgets import TkConfirmPopup, TkWarningPopup
from .input_widget import TkInputWidget, TkSearchBarWidget
from .output_widget import TkOutputWidget
from .tkinter_utils import bind_all_children


class TkTracker(ttk.PanedWindow):
    tracker_type: type[TrackerUI]
    input_widget_type = TkInputWidget
    output_widget_type = TkOutputWidget

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 orient: Literal['vertical', 'horizontal'] = 'horizontal',
                 ) -> None:
        super().__init__(parent, orient=orient)
        self.frame = ttk.Frame(self)
        self.add(self.frame)

        self.search_bar = TkSearchBarWidget(self.frame)
        self.search_bar.pack(fill='x')

        self.input_widget = self.input_widget_type(self.frame)
        self.input_widget.pack(expand=True, fill='both')

        self.output_widget = self.output_widget_type(self)
        self.add(self.output_widget)

        bind_all_children(
            self, '<Control-s>', lambda _: self.tracker.save_input_data())

        def on_configure(_: tk.Event) -> None:
            self.tracker.callback()
            width = self.sashpos(0)
            self.bind('<Double-Button-1>', lambda _: self.sashpos(0, width))
            self.unbind('<Configure>', func_id)

        func_id = self.bind('<Configure>', on_configure)

        self.tracker = self.tracker_type(
            configs=configs,
            parser=parser,
            input_widget=self.input_widget,
            output_widget=self.output_widget,
            search_bar=self.search_bar,
            warning_popup=TkWarningPopup(self, self.tracker_type.name),
            confirmation_popup=TkConfirmPopup(self, self.tracker_type.name),
            )

    def change_seed(self, seed: int, reload_notes: bool) -> None:
        self.tracker.change_seed(seed, reload_notes)
