import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import Protocol

from .. import __version__
from ..configs import Configs, UIWidgetConfigs
from ..data.file_functions import get_resource_path
from ..events.parser import EventParser
from ..gamestate import GameState
from ..logger import log_exceptions, log_tkinter_error
from ..tracker import FFXRNGTracker
from .actions_tracker import TkActionsTracker
from .base_widgets import DamageValuesDialogue
from .configslog import TkConfigsLogViewer
from .drops_tracker import TkDropsTracker
from .encounters_planner import TkEncountersPlanner
from .encounters_table import TkEncountersTable
from .encounters_tracker import TkEncountersTracker
from .monster_data_viewer import TkMonsterDataViewer
from .seed_info import TkSeedInfo
from .seedfinder import TkSeedFinder
from .status_tracker import TkStatusTracker
from .steps_tracker import TkStepsTracker
from .yojimbo_tracker import TkYojimboTracker


class TkTracker(Protocol):

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        ...

    def pack(self, *args, **kwargs) -> None:
        ...


@log_exceptions()
def main(*,
         title='FFX RNG tracker',
         size='1280x830',
         widget: type[TkTracker] | None = None,
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

    if widget is not None:
        parser = EventParser(GameState(FFXRNGTracker(seed)))
        name = WIDGET_NAMES[widget]
        configs = Configs.ui_widgets[name]
        ui = widget(root, parser, configs)
    else:
        ui = ttk.Notebook(root)
        for sub_widget, name in WIDGET_NAMES.items():
            configs = Configs.ui_widgets.get(name)
            if configs is None or not configs.shown:
                continue
            parser = EventParser(GameState(FFXRNGTracker(seed)))
            if configs.windowed:
                window = tk.Toplevel()
                window.title(name)
                window.geometry('1280x830')
                window.protocol('WM_DELETE_WINDOW', lambda: None)
                sub_widget(window, parser, configs).pack(expand=True, fill='both')
            else:
                ui.add(sub_widget(ui, parser, configs), text=name)

    ui.pack(expand=True, fill='both')

    root.deiconify()
    root.mainloop()


WIDGET_NAMES: dict[type[TkTracker], str] = {
    TkSeedInfo: 'Seed info',
    TkDropsTracker: 'Drops',
    TkEncountersTracker: 'Encounters',
    TkStepsTracker: 'Steps',
    TkEncountersPlanner: 'Encounters Planner',
    TkEncountersTable: 'Encounters Table',
    TkActionsTracker: 'Actions',
    TkStatusTracker: 'Status',
    TkYojimboTracker: 'Yojimbo',
    TkMonsterDataViewer: 'Monster Data',
    TkSeedFinder: 'Seedfinder',
    TkConfigsLogViewer: 'Configs/Log',
}

AZURE_THEME_DIRECTORY = os.path.dirname(__file__)
AZURE_THEME_PATH = 'azure_theme/azure.tcl'
