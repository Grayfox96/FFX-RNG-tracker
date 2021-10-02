import tkinter as tk

from ffx_rng_tracker.logger import (log_exceptions, log_tkinter_error,
                                    setup_logger)
from ffx_rng_tracker.ui_tkinter.monster_data_viewer import MonsterDataViewer


@log_exceptions()
def main():
    setup_logger()
    root = tk.Tk()
    root.protocol('WM_DELETE_WINDOW', lambda: root.quit())
    root.title('ffx_monster_data_viewer')
    root.geometry('1280x800')
    # redirects errors to another function
    root.report_callback_exception = log_tkinter_error
    ui = MonsterDataViewer(root)
    ui.pack(expand=True, fill='both')
    root.mainloop()


if __name__ == '__main__':
    main()
