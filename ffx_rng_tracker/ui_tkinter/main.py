import sys
import tkinter as tk
from tkinter import messagebox, ttk

from ..data.file_functions import get_resource_path
from ..logger import log_exceptions, log_tkinter_error, setup_logger
from .actions_tracker import ActionsTracker
from .base_widgets import DamageValuesDialogue
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

        windowed = messagebox.askyesno(
            'ffx_rng_tracker',
            'Show the encounters tracker as a separate window?')
        if windowed:
            window = tk.Toplevel()
            window.title('Encounters')
            self.encounters_tracker = EncountersTracker(window)
            self.encounters_tracker.pack(expand=True, fill='both')
        else:
            self.encounters_tracker = EncountersTracker(self)
            self.add(self.encounters_tracker, text='Encounters')

        self.damage_tracker = ActionsTracker(self)
        self.add(self.damage_tracker, text='Damage/crits/escapes/misses')

        self.status_tracker = StatusTracker(self)
        self.add(self.status_tracker, text='Status')

        if '-ps2' not in sys.argv:
            self.yojimbo_tracker = YojimboTracker(self)
            self.add(self.yojimbo_tracker, text='Yojimbo')

        self.monster_data_viewer = MonsterDataViewer(self)
        self.add(self.monster_data_viewer, text='Monster Data')


@log_exceptions()
def main(widget: type[tk.Widget], title='ffx_rng_tracker', size='1280x830'):
    """Creates a Tkinter main window, initializes the rng tracker
    and the root logger.
    """
    setup_logger()

    root = tk.Tk()
    # redirects errors to another function
    root.report_callback_exception = log_tkinter_error
    root.withdraw()
    root.protocol('WM_DELETE_WINDOW', root.quit)
    if '-ps2' in sys.argv:
        title += ' (ps2 mode)'
    root.title(title)
    root.geometry(size)

    if '-notheme' not in sys.argv:
        theme_path = get_resource_path(
            'ffx_rng_tracker/ui_tkinter/azure_theme/azure.tcl')
        root.tk.call('source', theme_path)
        if '-darkmode' in sys.argv:
            root.tk.call('set_theme', 'dark')
        else:
            root.tk.call('set_theme', 'light')

    entry_widget = DamageValuesDialogue(root, title=title)
    # if the entry widget was closed before initializing the tracker
    # close the program
    if entry_widget.rng_tracker is None:
        root.quit()
        sys.exit()

    ui = widget(root)

    ui.pack(expand=True, fill='both')

    root.deiconify()
    root.mainloop()
