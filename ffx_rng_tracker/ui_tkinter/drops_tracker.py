import tkinter as tk

from ffx_rng_tracker.events.parser import EventParser
from ffx_rng_tracker.gamestate import GameState
from ffx_rng_tracker.ui_abstract.drops_tracker import DropsTracker

from ..events.parsing_functions import (ParsingFunction, parse_bribe,
                                        parse_death, parse_kill,
                                        parse_party_change, parse_roll,
                                        parse_steal)
from .base_widgets import TkInputWidget, TkOutputWidget


class TkDropsOutputWidget(TkOutputWidget):

    def get_tags(self) -> dict[str, str]:
        tags = {
            'equipment': 'Equipment',
            'no encounters': 'No Encounters',
            'stat update': '^.*changed to.+$',
        }
        tags.update(super().get_tags())
        return tags


class TkDropsTracker(tk.Frame):
    """Widget used to track monster drops RNG."""

    def __init__(self, parent, seed: int, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        parser = EventParser(GameState(seed))
        for name, function in self.get_parsing_functions().items():
            parser.register_parsing_function(name, function)

        input_widget = TkInputWidget(self)
        input_widget.pack(fill='y', side='left')

        output_widget = TkDropsOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = DropsTracker(
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            )

        input_widget.register_callback(self.tracker.callback)

        self.tracker.callback()

    def get_parsing_functions(self) -> dict[str, ParsingFunction]:
        parsing_functions = {
            'roll': parse_roll,
            'waste': parse_roll,
            'advance': parse_roll,
            'steal': parse_steal,
            'kill': parse_kill,
            'death': parse_death,
            'party': parse_party_change,
            'bribe': parse_bribe,
        }
        return parsing_functions
