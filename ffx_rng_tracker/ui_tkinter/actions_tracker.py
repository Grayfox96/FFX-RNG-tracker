import tkinter as tk

from ..events.parser import EventParser
from ..events.parsing_functions import (ParsingFunction, parse_action,
                                        parse_encounter, parse_roll,
                                        parse_stat_update)
from ..gamestate import GameState
from ..ui_abstract.actions_tracker import ActionsTracker
from .base_widgets import TkInputWidget, TkOutputWidget


class TkActionsOutputWidget(TkOutputWidget):

    def get_tags(self) -> dict[str, str]:
        tags = {
            'encounter': 'Encounter',
            'preemptive': 'Preemptive',
            'ambush': 'Ambush',
            'crit': 'Crit',
            'stat update': '^.*changed to.+$',
        }
        tags.update(super().get_tags())
        return tags


class TkActionsTracker(tk.Frame):
    """Widget used to track damage, critical chance,
    escape chance and miss chance rng.
    """

    def __init__(self, parent, seed: int, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        parser = EventParser(GameState(seed))
        for name, function in self.get_parsing_functions().items():
            parser.register_parsing_function(name, function)

        input_widget = TkInputWidget(self)
        input_widget.pack(fill='y', side='left')

        output_widget = TkActionsOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = ActionsTracker(
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            )

        input_widget.register_callback(self.tracker.callback)

        self.tracker.callback()

    def get_parsing_functions(self) -> dict[str, ParsingFunction]:
        """Returns a dictionary with strings as keys
        and parsing functions as values.
        """
        parsing_functions = {
            'roll': parse_roll,
            'waste': parse_roll,
            'advance': parse_roll,
            'encounter': parse_encounter,
            'stat': parse_stat_update,
            'action': parse_action,
        }
        return parsing_functions
