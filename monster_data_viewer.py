import tkinter as tk
from tkinter import ttk

from ffx_rng_tracker import __version__
from ffx_rng_tracker.configs import Configs
from ffx_rng_tracker.data.constants import UIWidget
from ffx_rng_tracker.logger import (log_exceptions, log_tkinter_error,
                                    setup_main_logger)
from ffx_rng_tracker.ui_tkinter.help_window import show_help_window
from ffx_rng_tracker.ui_tkinter.monster_data_viewer import TkMonsterDataViewer
from ffx_rng_tracker.ui_tkinter.themes import cycle_theme, import_themes


@log_exceptions()
def main() -> None:
    root = tk.Tk()
    # redirects errors to another function
    root.report_callback_exception = log_tkinter_error
    root.protocol('WM_DELETE_WINDOW', root.quit)
    root.title('FFX Monster Data Viewer'
               f' v{__version__}'
               f' | Game Version: {Configs.game_version}'
               )

    import_themes(root)
    style = ttk.Style()
    if Configs.default_theme in style.theme_names():
        style.theme_use(Configs.default_theme)

    root.bind_all('<F1>', show_help_window)
    root.bind_all('<F8>', cycle_theme)

    ui_configs = Configs.ui_widgets[UIWidget.MONSTER_DATA]
    root.geometry(str(ui_configs.geometry))
    ui = TkMonsterDataViewer(root, ui_configs)
    ui.pack(expand=True, fill='both')

    ttk.Label(root, text='Press F1 for Help').place(relx=1, anchor='ne')
    root.mainloop()


if __name__ == '__main__':
    setup_main_logger()
    Configs.init_configs_from_user_files()
    main()
