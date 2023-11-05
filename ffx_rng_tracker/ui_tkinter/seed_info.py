import tkinter as tk

from ..data.constants import EquipmentType
from ..events.parser import EventParser
from ..ui_functions import get_equipment_types
from ..utils import treeview
from .output_widget import TkOutputWidget


class TkSeedInfoOutputWidget(TkOutputWidget):

    def get_regex_patterns(self) -> dict[str, str]:
        return {'equipment': str(EquipmentType.ARMOR)}


class TkSeedInfo(tk.Frame):
    """Widget that shows general information
    about the seed.
    """
    def __init__(self, parent, parser: EventParser, *args, **kwargs) -> None:
        super().__init__(parent, *args, *kwargs)

        self.output_widget = TkSeedInfoOutputWidget(self, wrap='none')
        self.output_widget.pack(expand=True, fill='both')
        seed = parser.gamestate.seed
        data = [
            f'Seed number: {seed}',
            get_equipment_types(seed, 50, 2),
        ]
        output = '\n\n'.join(data)

        self.output_widget.print_output(treeview(output))
