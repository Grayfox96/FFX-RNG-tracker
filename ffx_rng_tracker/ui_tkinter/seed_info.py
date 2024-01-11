import tkinter as tk

from ..configs import UIWidgetConfigs
from ..events.parser import EventParser
from ..ui_functions import get_equipment_types
from ..utils import treeview
from .output_widget import TkOutputWidget


class TkSeedInfo(tk.Frame):
    """Widget that shows general information
    about the seed.
    """
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
        seed = parser.gamestate.seed
        data = [
            f'Seed number: {seed}',
            get_equipment_types(seed, 50, 2),
        ]
        output = '\n\n'.join(data)

        output_widget.print_output(treeview(output))
