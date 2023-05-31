import os
import sys
import tkinter as tk
from tkinter import ttk

from .. import __version__
from ..configs import Configs
from ..data.file_functions import get_resource_path
from ..logger import log_exceptions, log_tkinter_error
from .actions_tracker import TkActionsTracker
from .base_widgets import DamageValuesDialogue
from .configslog import TkConfigsLogViewer
from .drops_tracker import TkDropsTracker
from .encounters_tracker import (TkEncountersPlanner, TkEncountersTable,
                                 TkEncountersTracker)
from .monster_data_viewer import TkMonsterDataViewer
from .seed_info import TkSeedInfo
from .seedfinder import TkSeedFinder
from .status_tracker import TkStatusTracker
from .steps_tracker import TkStepsTracker
from .yojimbo_tracker import TkYojimboTracker


class FFXRNGTrackerUI(ttk.Notebook):
    """Widget that contains all the other tracking widgets."""

    def __init__(self, parent, seed: int, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        widgets = self.get_widgets()
        for name, widget in widgets.items():
            configs = Configs.ui_widgets.get(name)
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

    def get_widgets(self) -> dict[str, type[tk.Widget]]:
        widgets = {
            'Seed info': TkSeedInfo,
            'Drops': TkDropsTracker,
            'Encounters': TkEncountersTracker,
            'Steps': TkStepsTracker,
            'Encounters Planner': TkEncountersPlanner,
            'Encounters Table': TkEncountersTable,
            'Actions': TkActionsTracker,
            'Status': TkStatusTracker,
            'Yojimbo': TkYojimboTracker,
            'Monster Data': TkMonsterDataViewer,
            'Seedfinder': TkSeedFinder,
            'Configs/Log': TkConfigsLogViewer,
        }
        return widgets


@log_exceptions()
def main(widget: type[tk.Widget],
         title='FFX RNG tracker',
         size='1280x830',
         ) -> None:
    """Creates a Tkinter main window, initializes the rng tracker
    and the root logger.
    """
    root = tk.Tk()
    # redirects errors to another function
    root.report_callback_exception = log_tkinter_error
    root.withdraw()
    root.protocol('WM_DELETE_WINDOW', root.quit)
    title += (f' v{__version__} {Configs.game_version} '
              f'Category: {Configs.speedrun_category}')
    root.title(title)
    root.geometry(size)

    if Configs.use_theme:
        theme_path = get_resource_path(
            relative_path=AZURE_THEME_PATH,
            file_directory=AZURE_THEME_DIRECTORY
            )
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


AZURE_THEME_DIRECTORY = os.path.dirname(__file__)
AZURE_THEME_PATH = 'azure_theme/azure.tcl'
