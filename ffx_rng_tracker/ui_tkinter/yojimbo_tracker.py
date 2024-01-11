import tkinter as tk

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_abstract.yojimbo_tracker import YojimboTracker
from .base_widgets import TkConfirmPopup, TkWarningPopup
from .input_widget import TkInputWidget, TkSearchBarWidget
from .output_widget import TkOutputWidget


class TkYojimboTracker(tk.Frame):

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

        input_widget = TkInputWidget(frame)
        input_widget.pack(expand=True, fill='y')
        input_widget.text.bind(
            '<Control-s>', lambda _: self.tracker.save_input_data())

        output_widget = TkOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = YojimboTracker(
            configs=configs,
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            search_bar=search_bar,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            )
        self.tracker.callback()
