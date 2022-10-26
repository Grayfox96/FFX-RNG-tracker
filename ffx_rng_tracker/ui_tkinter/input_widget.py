import tkinter as tk
from tkinter import font
from typing import Callable

from .base_widgets import ScrollableText, get_default_font_args


class TkInputWidget(ScrollableText):

    def __init__(self, parent, *args, **kwargs) -> None:
        kwargs.setdefault('font', font.Font(**get_default_font_args()))
        kwargs.setdefault('width', 40)
        kwargs.setdefault('undo', True)
        kwargs.setdefault('autoseparators', True)
        kwargs.setdefault('maxundo', -1)
        super().__init__(parent, *args, **kwargs)

        self.focused = tk.BooleanVar(value=False)
        self.bind('<FocusIn>', lambda _: self.focused.set(True))
        self.bind('<FocusOut>', lambda _: self.focused.set(False))

    def get_input(self) -> str:
        return self.get('1.0', 'end')

    def set_input(self, text: str) -> None:
        self.set(text)

    def register_callback(self, callback_func: Callable) -> None:
        callback_func()
        delay = 1000 - (990 * self.focused.get())
        self.after(delay, self.register_callback, callback_func)


class TkSearchBarWidget(tk.Entry):

    def get_input(self) -> str:
        return self.get()

    def set_input(self, text: str) -> None:
        self.delete('1', 'end')
        self.insert('1', text)

    def register_callback(self, callback_func: Callable) -> None:
        self.bind('<KeyRelease>', callback_func)
