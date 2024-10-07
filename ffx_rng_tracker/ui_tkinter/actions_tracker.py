from tkinter import ttk

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_abstract.actions_tracker import ActionsTracker
from .base_widgets import TkConfirmPopup, TkWarningPopup
from .input_widget import TkInputWidget, TkSearchBarWidget
from .output_widget import TkOutputWidget
from .tkinter_utils import bind_all_children


class TkActionsTracker(ttk.Frame):

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

        input_widget = TkInputWidget(frame)
        input_widget.pack(expand=True, fill='y')

        output_widget = TkOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')

        bind_all_children(
            self, '<Control-s>', lambda _: self.tracker.save_input_data())

        self.tracker = ActionsTracker(
            configs=configs,
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            search_bar=search_bar,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            )
        self.tracker.callback()
