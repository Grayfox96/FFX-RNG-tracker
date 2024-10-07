import tkinter as tk
from collections import deque
from collections.abc import Callable
from typing import Any, Literal

from ..configs import Configs


def create_command_proxy(widget: tk.Widget,
                         triggers: set[str],
                         callback_func: Callable[[], None],
                         ) -> None:
    """Used to assign a function to a widget that intercepts commands and
    calls callback_func if the command is in triggers.

    Renames the widget to f'{str(widget)}_proxied' by calling
    widget.tk.call('rename', ...), the widget will be renamed only once.
    https://www.tcl.tk/man/tcl8.6/TclCmd/rename.html
    """
    # str(widget) will be the original name
    # even if the widget has been renamed already
    old_name = str(widget)
    new_name = old_name + '_proxied'
    # rename the widget so it can keep it's old functionality
    try:
        widget.tk.call('rename', old_name, new_name)
    except tk.TclError:
        pass

    def command_proxy(command: str, *args: str) -> Any:
        try:
            result = widget.tk.call((new_name, command) + args)
        except tk.TclError as e:
            # the return value when an error occurs doesn't seem to matter
            result = str(e)
            # fixes a bug with ttk.Entry
            if result == 'can\'t read "w": no such variable':
                new_args = [a.replace('$w', old_name) for a in args]
                result = command_proxy(command, *new_args)
        if command in triggers:
            # if there are calls on the queue cancel them
            while scheduled_callbacks:
                widget.after_cancel(scheduled_callbacks.popleft())
            scheduled_callbacks.append(widget.after(10, callback_func))
        return result

    # used to prevent multiple back-to-back calls to go through
    # and to prevent multiple triggers to stall the tkinter engine
    scheduled_callbacks: deque[str] = deque()
    # intercept calls to the old name
    widget.tk.createcommand(old_name, command_proxy)


def bind_all_children(widget: tk.Widget,
                      sequence: str,
                      callback: Callable[[tk.Event], Any],
                      add: bool | Literal['', '+'] = '',
                      ) -> None:
    widgets: list[tk.Widget] = [widget]
    while widgets:
        widget = widgets.pop()
        widget.bind(sequence, callback, add)
        widgets.extend(list(widget.children.values()))


def get_default_font() -> tuple[str, int]:
    return 'Courier New', Configs.font_size
