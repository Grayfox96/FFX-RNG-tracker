import sys
import tkinter as tk
from tkinter import ttk
from typing import Type

from ..configs import Configs
from ..data.file_functions import get_resource_path
from ..logger import log_exceptions, log_tkinter_error, setup_logger
from ..main import get_tracker
from .actions_tracker import ActionsTracker
from .base_widgets import DamageValuesDialogue
from .configs import ConfigsPage
from .drops_tracker import DropsTracker
from .encounters_tracker import EncountersTracker
from .monster_data_viewer import MonsterDataViewer
from .seed_info import SeedInfo
from .status_tracker import StatusTracker
from .yojimbo_tracker import YojimboTracker


class FFXRNGTrackerUI(ttk.Notebook):
    """Widget that contains all the other tracking widgets."""

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.seed_info = SeedInfo(self)
        self.add(self.seed_info, text='Seed info')

        self.drops_tracker = DropsTracker(self)
        self.add(self.drops_tracker, text='Drops')

        if Configs.windowed_enc_tracker:
            window = tk.Toplevel()
            window.title('Encounters')
            window.protocol("WM_DELETE_WINDOW", lambda: None)
            self.encounters_tracker = EncountersTracker(window)
            self.encounters_tracker.pack(expand=True, fill='both')
        else:
            self.encounters_tracker = EncountersTracker(self)
            self.add(self.encounters_tracker, text='Encounters')

        self.damage_tracker = ActionsTracker(self)
        self.add(self.damage_tracker, text='Damage/crits/escapes/misses')

        self.status_tracker = StatusTracker(self)
        self.add(self.status_tracker, text='Status')

        self.yojimbo_tracker = YojimboTracker(self)
        self.add(self.yojimbo_tracker, text='Yojimbo')

        self.monster_data_viewer = MonsterDataViewer(self)
        self.add(self.monster_data_viewer, text='Monster Data')

        self.configs_page = ConfigsPage(self)
        self.add(self.configs_page, text='Configs')


@log_exceptions()
def main(widget: Type[tk.Widget], title='ffx_rng_tracker', size='1280x830'):
    """Creates a Tkinter main window, initializes the rng tracker
    and the root logger.
    """
    setup_logger()

    root = tk.Tk()
    # redirects errors to another function
    root.report_callback_exception = log_tkinter_error
    root.withdraw()
    root.protocol('WM_DELETE_WINDOW', root.quit)
    if Configs.ps2:
        title += ' (ps2 mode)'
    root.title(title)
    root.geometry(size)

    if Configs.use_theme:
        theme_path = get_resource_path(
            'ffx_rng_tracker/ui_tkinter/azure_theme/azure.tcl')
        root.tk.call('source', theme_path)
        if Configs.use_dark_mode:
            root.tk.call('set_theme', 'dark')
        else:
            root.tk.call('set_theme', 'light')

    if Configs.seed is None:
        entry_widget = DamageValuesDialogue(root, title=title)
        # if the entry widget was closed before initializing the tracker
        # close the program
        if entry_widget.rng_tracker is None:
            root.quit()
            sys.exit()
    else:
        get_tracker(Configs.seed)

    ui = widget(root)

    ui.pack(expand=True, fill='both')

    root.deiconify()
    root.mainloop()
