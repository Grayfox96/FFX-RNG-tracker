import tkinter as tk
from tkinter import ttk

from .. import __version__
from ..configs import Configs
from ..data.constants import UIWidget
from ..events.parser import EventParser
from ..gamestate import GameState
from ..logger import log_exceptions, log_tkinter_error
from ..tracker import FFXRNGTracker
from .help_window import show_help_window
from .seed_info import TkSeedInfo
from .themes import cycle_theme, import_themes
from .tktracker import TkTracker
from .trackersnotebook import TkTrackersNotebook


@log_exceptions()
def main(*,
         title='FFX RNG tracker',
         widget: type[TkTracker] | None = None,
         ) -> None:
    """Creates a Tkinter main window, initializes the rng tracker
    and the root logger.
    """
    root = tk.Tk()
    # redirects errors to another function
    root.report_callback_exception = log_tkinter_error
    root.protocol('WM_DELETE_WINDOW', root.quit)
    title += (f' v{__version__}'
              f' | Game Version: {Configs.game_version}'
              f' | Category: {Configs.speedrun_category}'
              )
    root.title(title)

    import_themes(root)
    style = ttk.Style()
    if Configs.default_theme in style.theme_names():
        style.theme_use(Configs.default_theme)

    root.bind_all('<F1>', show_help_window)
    root.bind_all('<F8>', cycle_theme)

    if widget is None:
        root.geometry(str(Configs.ui_widgets[UIWidget.SEED_INFO].geometry))
        ui = TkTrackersNotebook(root)
        ui.pack(expand=True, fill='both')
    else:
        root.geometry(str(Configs.ui_widgets[widget.tracker_type.name].geometry))
        ui = TkSeedInfo(root, Configs.ui_widgets[UIWidget.SEED_INFO])
        ui.pack(expand=True, fill='both')

        def callback_func(seed: int, _: bool) -> None:
            parser = EventParser(GameState(FFXRNGTracker(seed)))
            name = widget.tracker_type.name
            configs = Configs.ui_widgets[name]
            new_ui = widget(root, parser, configs)
            ui.forget()
            new_ui.pack(expand=True, fill='both')
            root.title(f'{title} | Seed: {seed}')

        if Configs.seed is None:
            ui.register_callback(callback_func)
        else:
            callback_func(Configs.seed, True)

    ttk.Label(root, text='Press F1 for Help').place(relx=1, anchor='ne')
    root.mainloop()
