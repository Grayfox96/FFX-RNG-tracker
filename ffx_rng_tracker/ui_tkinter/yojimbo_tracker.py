import tkinter as tk

from ..events.parser import EventParser
from ..ui_abstract.yojimbo_tracker import YojimboTracker
from .base_widgets import TkConfirmPopup, TkWarningPopup
from .input_widget import TkInputWidget
from .output_widget import TkOutputWidget


class TkYojimboOutputWidget(TkOutputWidget):

    def get_regex_patterns(self) -> dict[str, str]:
        tags = {
            'yojimbo low gil': r'\m[0-9]{1,7}(?= gil )',
            'yojimbo high gil': r'\m[0-9]{10,}(?= gil )',
            'compatibility update': '^Compatibility: .+$',
        }
        tags.update(super().get_regex_patterns())
        return tags


class TkYojimboTracker(tk.Frame):

    def __init__(self, parent, parser: EventParser, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        input_widget = TkInputWidget(self)
        input_widget.pack(fill='y', side='left')
        input_widget.bind(
            '<Control-s>', lambda _: self.tracker.save_input_data())

        output_widget = TkYojimboOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = YojimboTracker(
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            )
