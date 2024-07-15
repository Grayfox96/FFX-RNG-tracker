import logging
import tkinter as tk

from ..configs import Configs, UIWidgetConfigs
from ..logger import UIHandler
from ..utils import treeview
from .output_widget import TkOutputWidget


class TkConfigsLogViewer(tk.Frame):
    """Widget that shows the loaded configuration and the log."""

    def __init__(self,
                 parent,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        tk.Label(self, text='Configs').grid(row=0, column=0, sticky='nsew')
        tk.Label(self, text='Log').grid(row=0, column=1, sticky='nsew')
        self.rowconfigure(1, weight=1)
        self.columnconfigure(1, weight=1)

        self.configs = TkOutputWidget(self, wrap='none', width=80)
        for name in configs.tag_names:
            self.configs.register_tag(name)
        self.configs.grid(row=1, column=0, sticky='nsew')
        self.configs.print_output(treeview(Configs.get_configs()))

        self.logger = TkOutputWidget(self, wrap='none')
        for name in configs.tag_names:
            self.logger.register_tag(name)
        self.logger.grid(row=1, column=1, sticky='nsew')

        self.handler = UIHandler(self.logger)
        formatter = logging.Formatter(
            fmt='{asctime} - {levelname} - {message}',
            datefmt='%H:%M:%S',
            style='{',
            )
        self.handler.setFormatter(formatter)
        self.handler.setLevel(logging.INFO)
        logging.getLogger(__name__.split('.')[0]).addHandler(self.handler)
