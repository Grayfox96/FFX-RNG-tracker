import tkinter as tk

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_functions import get_status_chance_table
from .output_widget import TkOutputWidget


class TkStatusTracker(tk.Frame):
    """Widget that shows status RNG rolls."""

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        output_widget = TkOutputWidget(self, wrap='none')
        for name in configs.tag_names:
            output_widget.register_tag(name)
        output_widget.pack(expand=True, fill='both')
        table = get_status_chance_table(parser.gamestate.seed, 100)
        output_widget.print_output(table)
