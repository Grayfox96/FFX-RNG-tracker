import re
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from .tkinter_utils import create_command_proxy


class ScrollableText(tk.Frame):
    """Frame widget with a Text and a vertical Scrollbar
    and an optional horizontal Scrollbar.

    Parameter "parent" will be passed to the Frame __init__ method.
    All other parameters will be passed to the internal Text __init__ method.
    If parameter "wrap" is set to "none" the add_h_scrollbar method
    will be called.

    Call the add_h_scrollbar method to add the horizontal Scrollbar manually.
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent)
        self.bind('<<ThemeChanged>>', self.on_theme_changed)
        self.h_scrollbar: ttk.Scrollbar | None = None
        self.v_scrollbar = ttk.Scrollbar(self)
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        kwargs['yscrollcommand'] = self.v_scrollbar.set
        self.text = tk.Text(self, *args, **kwargs)
        self.v_scrollbar.configure(command=self.text.yview)
        self.text.grid(row=0, column=0, sticky='nsew')
        if kwargs.get('wrap') == 'none':
            self.add_h_scrollbar()

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._old_seek_text = ''
        self._old_seek_index = '1.0'
        self.text.tag_configure(
            tagName='#seek',
            borderwidth='1',
            relief='solid',
            )

    def add_h_scrollbar(self) -> None:
        if self.h_scrollbar is not None:
            return
        self.h_scrollbar = ttk.Scrollbar(self, orient='horizontal')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.text.configure(xscrollcommand=self.h_scrollbar.set)
        self.h_scrollbar.configure(command=self.text.xview)

    def highlight_pattern(self,
                          tag_name: str,
                          pattern: re.Pattern,
                          text: str | None = None,
                          ) -> None:
        """Apply the tag named tag_name to all occurrences
        of the pattern.

        Tk implementation: accepts a text parameter, if text is
        not provided self.text.get() will be called.
        """
        if text is None:
            text = self.text.get('1.0', 'end')
        spans: list[str] = []
        for i, line in enumerate(text.splitlines(), 1):
            for m in pattern.finditer(line):
                start, end = m.span()
                spans.extend((f'{i}.{start}', f'{i}.{end}'))
        if not spans:
            return
        self.text.tag_add(tag_name, *spans)

    def set(self, text: str) -> None:
        """Replaces the previous text and scrolls back to
        the previous position.
        """
        current_text = self.text.get('1.0', 'end')[:-1]
        current_number_of_lines = len(current_text.splitlines())
        last_line = self.text.index(f'@0,{self.winfo_height()}')
        line_index = int(last_line.split('.')[0])

        self.text.replace(1.0, 'end', text)

        # scroll down if the last line of the text was visible
        # but only if there was at least 1 line
        if line_index == current_number_of_lines and line_index > 1:
            self.text.yview_pickplace('end')

    def seek(self, text: str) -> None:
        self.text.tag_remove('#seek', '1.0', 'end')
        if not text:
            self._old_seek_text = ''
            return
        if text == self._old_seek_text:
            start = self._old_seek_index
        else:
            start = self.text.index('@0,0')
            self._old_seek_text = text
        index = self.text.search(text, start, 'end', nocase=True)
        if not index:
            index = self.text.search(text, '1.0', start, nocase=True)
            if not index:
                return
        self._old_seek_index = f'{index}+1c'
        self.text.see(index)
        self.text.tag_add('#seek', index, f'{index}+{len(text)}c')

    def on_theme_changed(self, event: tk.Event) -> None:
        style = ttk.Style()
        fg = style.configure('.', 'foreground')
        bg = style.configure('.', 'background')
        fg_rgb = self.winfo_rgb(fg)
        # fg_rgb is a tuple of values from 0 to 0xffff
        if fg_rgb < (0xff, 0xff, 0xff):
            bg = '#ffffff'
        self.text.configure(foreground=fg, background=bg)


class BetterSpinbox(ttk.Spinbox):
    """Upgraded Spinbox widget with a set method
    and readonly by default.
    """

    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.set(0)

    def set(self, text: str | int) -> None:
        """Set the spinbox content."""
        self.config(state='normal')
        self.delete(0, 'end')
        self.insert(0, text)
        self.config(state='readonly')

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self, {'set'}, callback_func)


class ScrollableFrame(ttk.Frame):
    """"""

    def __init__(self, parent, *args, **kwargs) -> None:
        self.parent = parent
        self.outer_frame = ttk.Frame(parent)
        self.canvas = tk.Canvas(
            self.outer_frame, width=280, highlightthickness=0)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.bind('<<ThemeChanged>>', self.on_theme_changed)
        scrollbar = ttk.Scrollbar(
            self.outer_frame, orient='vertical', command=self.canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.canvas.config(yscrollcommand=scrollbar.set)
        super().__init__(self.canvas, *args, **kwargs)
        super().pack(fill='both', expand=True)
        self.bind(
            '<Configure>',
            lambda _: self.canvas.config(scrollregion=self.canvas.bbox('all')))
        self.canvas.create_window((0, 0), window=self, anchor='nw')
        # when the mouse enters the canvas it binds the mousewheel to scroll
        self.canvas.bind(
            '<Enter>',
            lambda _: self.canvas.bind_all(
                '<MouseWheel>',
                lambda e: self.canvas.yview_scroll(
                    int(-1 * (e.delta / 120)), 'units')))
        # when the mouse leaves the canvas it unbinds the mousewheel
        self.canvas.bind(
            '<Leave>', lambda _: self.canvas.unbind_all('<MouseWheel>'))
        self.pack = self.outer_frame.pack
        self.grid = self.outer_frame.grid

    def on_theme_changed(self, event: tk.Event) -> None:
        style = ttk.Style()
        bg = style.configure('.', 'background')
        self.canvas.configure(background=bg)


class BetterScale(ttk.Scale):
    """Scale widget that sets itself to an integer value
    when manually set with the mouse.
    """
    def __init__(self, parent: tk.Widget, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)
        self.bind('<ButtonRelease>', self.on_release)

    def get_input(self) -> int:
        return int(round(self.get()))

    def on_release(self, event: tk.Event) -> None:
        value = self.get_input()
        self.configure(value=value)

    def register_callback(self, callback_func: Callable[[], None]) -> None:
        create_command_proxy(self, {'set'}, callback_func)


class TkWarningPopup:

    def print_output(self, output: str) -> None:
        messagebox.showwarning(message=output)


class TkConfirmPopup:

    def print_output(self, output: str) -> bool:
        return messagebox.askokcancel(message=output)
