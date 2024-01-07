import tkinter as tk

from ..events.parser import EventParser
from ..ui_functions import get_status_chance_table
from .output_widget import TkOutputWidget


class TkStatusTrackerOutputWidget(TkOutputWidget):

    def get_regex_patterns(self) -> dict[str, str]:
        return {'status miss': r'\m100\M'}


class TkStatusTracker(tk.Frame):
    """Widget that shows status RNG rolls."""

    def __init__(self, parent, parser: EventParser, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        self.output_widget = TkStatusTrackerOutputWidget(self, wrap='none')
        self.output_widget.pack(expand=True, fill='both')
        self.output_widget.print_output(get_status_chance_table(parser.gamestate.seed, 100))
