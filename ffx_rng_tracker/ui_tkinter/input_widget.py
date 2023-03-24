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

    def get_input(self) -> str:
        return self.get('1.0', 'end')

    def set_input(self, text: str) -> None:
        self.set(text)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        def callback_func_after(_: tk.Event):
            while scheduled_callbacks:
                self.after_cancel(scheduled_callbacks.pop(0))
            scheduled_callbacks.append(self.after(100, callback_func))

        scheduled_callbacks: list[str] = []
        self.bind('<KeyRelease>', callback_func_after)


class TkSearchBarWidget(tk.Entry):

    def get_input(self) -> str:
        return self.get()

    def set_input(self, text: str) -> None:
        self.delete('1', 'end')
        self.insert('1', text)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        self.bind('<KeyRelease>', callback_func)
