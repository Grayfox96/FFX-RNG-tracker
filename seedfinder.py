import tkinter as tk

from ffx_rng_tracker.configs import Configs
from ffx_rng_tracker.data.file_functions import get_resource_path, get_version
from ffx_rng_tracker.logger import (log_exceptions, log_tkinter_error,
                                    setup_logger)
from ffx_rng_tracker.main import get_tracker
from ffx_rng_tracker.ui_tkinter.main import AZURE_THEME_PATH
from ffx_rng_tracker.ui_tkinter.seedfinder import SeedFinder


@log_exceptions()
def main():
    setup_logger()
    root = tk.Tk()
    root.report_callback_exception = log_tkinter_error
    root.protocol('WM_DELETE_WINDOW', root.quit)
    title = 'ffx_seedfinder v' + '.'.join(get_version())
    if Configs.ps2:
        title += ' (ps2 mode)'
    root.title(title)
    root.geometry('800x600')

    if Configs.use_theme:
        theme_path = get_resource_path(AZURE_THEME_PATH)
        root.tk.call('source', theme_path)
        if Configs.use_dark_mode:
            root.tk.call('set_theme', 'dark')
        else:
            root.tk.call('set_theme', 'light')

    get_tracker(0)
    ui = SeedFinder(root)
    ui.pack(expand=True, fill='both')
    root.mainloop()


if __name__ == '__main__':
    main()
