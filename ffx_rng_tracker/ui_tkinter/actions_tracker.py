import tkinter as tk

from ..ui_abstract.actions_tracker import ActionsTracker
from .input_widget import TkInputWidget
from .output_widget import TkOutputWidget


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

    def __init__(self, parent, seed: int, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        input_widget = TkInputWidget(self)
        input_widget.pack(fill='y', side='left')

        output_widget = TkActionsOutputWidget(self)
        output_widget.pack(expand=True, fill='both', side='right')

        self.tracker = ActionsTracker(
            seed=seed,
            input_widget=input_widget,
            output_widget=output_widget,
            )
