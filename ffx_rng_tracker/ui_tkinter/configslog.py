import logging
import re
from dataclasses import is_dataclass
from tkinter import ttk
from typing import Any, Iterator

from ..configs import Configs, UIWidgetConfigs
from ..logger import UIHandler
from .output_widget import TkOutputWidget


def add_dict_to_treeview(treeview: ttk.Treeview,
                         k_v_pairs: Iterator[tuple[str | int, Any]],
                         parent: str = '',
                         ) -> None:
    for k, v in k_v_pairs:
        k = str(k)
        match v:
            case dict():
                if v:
                    iid = treeview.insert(parent, 'end', text=k)
                    add_dict_to_treeview(treeview, v.items(), iid)
                    continue
                text, value = f'{k}{{}}', 'Empty'
            case _ if is_dataclass(v):
                v = vars(v)
                if v:
                    iid = treeview.insert(parent, 'end', text=k)
                    add_dict_to_treeview(treeview, v.items(), iid)
                    continue
                text, value = f'{k}{{}}', 'Empty'
            case list() | tuple() | set():
                if v:
                    iid = treeview.insert(parent, 'end', text=f'{k}[]')
                    add_dict_to_treeview(treeview, enumerate(v), iid)
                    continue
                text, value = f'{k}[]', 'Empty'
            case str() if '\n' in v:
                line, *lines = f'\'{v}\''.splitlines()
                iid = treeview.insert(parent, 'end', text=k, values=(line,))
                for line in lines:
                    treeview.insert(iid, 'end', values=(f' {line}',))
                continue
            case re.Pattern():
                text, value = k, f'\'{v.pattern}\''
            case int() | None:  # also catches float and bool
                text, value = k, f'{v}'
            case str():
                text, value = k, f'\'{v}\''
            case _:
                raise TypeError(f'Type not supported for v: {type(v)}')
        iid = treeview.insert(parent, 'end', text=text, values=(value,))


class TkConfigsLogViewer(ttk.Frame):
    """Widget that shows the loaded configuration and the log."""

    def __init__(self,
                 parent,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        ttk.Label(self, text='Configs').grid(row=0, column=0)
        ttk.Label(self, text='Log').grid(row=0, column=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.configs = ttk.Treeview(self, columns='Values', show='tree')
        self.configs.column('#0', anchor='w')
        self.configs.column('Values', anchor='w')
        add_dict_to_treeview(self.configs, Configs.get_configs().items())
        self.configs.grid(row=1, column=0, sticky='nsew')

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
