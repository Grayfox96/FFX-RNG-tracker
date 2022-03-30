import sys
import tkinter as tk
from tkinter import ttk

from ..configs import Configs
from ..data.file_functions import get_resource_path, get_version
from ..logger import log_exceptions, log_tkinter_error, setup_logger
from .actions_tracker import ActionsTracker
from .base_widgets import BaseTracker, DamageValuesDialogue
from .configs import ConfigsPage
from .drops_tracker import DropsTracker
from .encounters_tracker import (EncountersPlanner, EncountersTable,
                                 EncountersTracker)
from .monster_actions_tracker import MonsterActionsTracker
from .monster_data_viewer import MonsterDataViewer
from .seed_info import SeedInfo
from .status_tracker import StatusTracker
from .yojimbo_tracker import YojimboTracker


class FFXRNGTrackerUI(ttk.Notebook):
    """Widget that contains all the other tracking widgets."""

    def __init__(self, parent, seed: int, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        widgets = self.get_widgets()
        for name, widget in widgets.items():
            configs = Configs.ui_widgets.get(name, None)
            if configs is None or not configs.shown:
                continue
            if configs.windowed:
                window = tk.Toplevel()
                window.title(name)
                window.geometry('1280x830')
                window.protocol('WM_DELETE_WINDOW', lambda: None)
                widget(window, seed).pack(expand=True, fill='both')
            else:
                self.add(widget(self, seed), text=name)

    def get_widgets(self) -> dict[str, type[BaseTracker]]:
        widgets = {
            'Seed info': SeedInfo,
            'Drops': DropsTracker,
            'Encounters': EncountersTracker,
            'Encounters Table': EncountersTable,
            'Encounters Planner': EncountersPlanner,
            'Damage/crits/escapes/misses': ActionsTracker,
            'Monster Targeting': MonsterActionsTracker,
            'Status': StatusTracker,
            'Yojimbo': YojimboTracker,
            'Monster Data': MonsterDataViewer,
            'Configs': ConfigsPage,
        }
        return widgets


@log_exceptions()
def main(widget: type[BaseTracker],
         title='ffx_rng_tracker',
         size='1280x830',
         ) -> None:
    """Creates a Tkinter main window, initializes the rng tracker
    and the root logger.
    """
    setup_logger()

    root = tk.Tk()
    # redirects errors to another function
    root.report_callback_exception = log_tkinter_error
    root.withdraw()
    root.protocol('WM_DELETE_WINDOW', root.quit)
    title += ' v' + '.'.join(map(str, get_version()))
    if Configs.ps2:
        title += ' (ps2 mode)'
    root.title(title)
    root.geometry(size)

    if Configs.use_theme:
        theme_path = get_resource_path(AZURE_THEME_PATH)
        root.tk.call('source', theme_path)
        if Configs.use_dark_mode:
            root.tk.call('set_theme', 'dark')
        else:
            root.tk.call('set_theme', 'light')

    if Configs.seed is None:
        entry_widget = DamageValuesDialogue(root, title=title)
        # if the entry widget was closed before finding a seed
        # close the program
        if entry_widget.seed is None:
            root.quit()
            sys.exit()
        seed = entry_widget.seed
    else:
        seed = Configs.seed

    ui = widget(root, seed)

    ui.pack(expand=True, fill='both')

    root.deiconify()
    root.mainloop()


AZURE_THEME_PATH = 'ui_tkinter/azure_theme/azure.tcl'
