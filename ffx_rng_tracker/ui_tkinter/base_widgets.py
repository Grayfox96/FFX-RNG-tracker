import sys
import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import font, simpledialog
from tkinter.scrolledtext import ScrolledText
from typing import Union

from ..errors import InvalidDamageValueError, SeedNotFoundError
from ..tracker import get_tracker


class BetterText(ScrolledText):
    """Upgraded ScrolledText widget with an highlight_pattern
    method and a set method.
    """

    def highlight_pattern(
            self, pattern: str, tag: str, start: str = '1.0',
            end: str = 'end', regexp: bool = False) -> None:
        """Apply the given tag to all occurrences of the pattern."""
        start = self.index(start)
        end = self.index(end)
        self.mark_set('matchStart', start)
        self.mark_set('matchEnd', start)
        self.mark_set('searchLimit', end)
        count = tk.IntVar()
        while True:
            index = self.search(
                pattern, 'matchEnd', 'searchLimit', count=count, regexp=regexp)
            if index == '' or count.get() == 0:
                break
            self.mark_set('matchStart', index)
            self.mark_set('matchEnd', f'{index}+{count.get()}c')
            self.tag_add(tag, 'matchStart', 'matchEnd')

    def set(self, text: str) -> None:
        # if the current text is the same as the new text do nothing
        # a newline character gets automatically added
        # so it needs to be removed to compare
        current_text = self.get('1.0', 'end')[:-1]
        if text == current_text:
            return
        # get the index of the middle and last visible lines
        height = self.winfo_height()
        middle_line = self.index(f'@0,{height // 2}')
        last_line = self.index(f'@0,{height}')
        middle_line_index = int(middle_line.split('.')[0])
        last_line_index = int(last_line.split('.')[0])
        # calculate the number of visible lines
        visible_lines = (last_line_index - middle_line_index) * 2

        # overwrite the content
        self.delete(1.0, 'end')
        self.insert(1.0, text)

        number_of_lines = int(self.index('end').split('.')[0]) - 1
        # if the saved position is too close to the top
        # and there are enough lines in the text
        # scroll to the bottom first
        if (middle_line_index < visible_lines * 2
                and number_of_lines > visible_lines * 2):
            self.see('end')
        # scroll back to the position before the text was overwritten
        self.see(middle_line)


class BetterSpinbox(tk.Spinbox):
    """Upgraded Spinbox widget with a set method
    and readonly by default.
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.config(state='readonly')

    def set(self, text: Union[str, int]) -> None:
        """Set the spinbox content."""
        self.config(state='normal')
        self.delete(0, 'end')
        self.insert(0, text)
        self.config(state='readonly')


class BaseWidget(tk.Frame, ABC):
    """Abstract base class for all tkinter widgets."""

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        self.font = font.Font(family='Courier New', size=9)
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.rng_tracker = get_tracker()
        self.input_widget = self.make_input_widget()
        self.output_widget = self.make_output_widget()
        self.print_output()

    def make_input_widget(self) -> BetterText:
        """Initializes input widget."""
        text = BetterText(
            self, font=self.font, width=40, undo=True, autoseparators=True,
            maxundo=-1)
        text.pack(fill='y', side='left')
        text.bind('<KeyRelease>', lambda _: self.print_output())
        return text

    def make_output_widget(self) -> BetterText:
        """Initialize output widget."""
        text = BetterText(self, font=self.font, state='disabled', wrap='word')
        text.pack(expand=True, fill='both', side='right')

        text.tag_configure('red', foreground='#ff0000')
        text.tag_configure('green', foreground='#00ff00')
        text.tag_configure('blue', foreground='#0000ff')
        text.tag_configure('yellow', foreground='#beb144')
        text.tag_configure('gray', foreground='#888888')
        text.tag_configure('red_background', background='#ff0000')
        text.tag_configure('wrap_margin', lmargin2='1c')
        text.tag_configure(
            'highlight', background='#ffff00', foreground='#000000',
            selectforeground='#000000')

        return text

    @abstractmethod
    def get_input(self):
        """Parse the input widget text and add events to the tracker."""

    @abstractmethod
    def print_output(self):
        """Get information from the events sequence, highlight keywords."""


class DamageValuesDialogue(simpledialog.Dialog):
    """Input dialogue used to get damage values."""

    def __init__(self, *args, **kwargs):
        self.warning_label = False
        self.rng_tracker = None
        super().__init__(*args, **kwargs)

    def body(self, parent: tk.Tk):
        self.parent = parent
        if '-ps2' in sys.argv:
            text = 'Seed number'
        else:
            text = 'Damage values (Auron1 Tidus1 A2 T2 A3 T3)'
        tk.Label(parent, text=text).pack()
        self.entry = tk.Entry(parent, width=25)
        self.entry.pack(fill='x')
        return self.entry

    def buttonbox(self) -> None:
        tk.Button(self, text='Submit', command=self.validate_input).pack()
        self.bind('<Return>', lambda _: self.validate_input())
        self.bind('<Escape>', lambda _: self.parent.quit())

    def validate_input(self) -> None:
        input_string = self.entry.get()
        # replace different symbols with spaces
        for symbol in (',', '-', '/', '\\'):
            input_string = input_string.replace(symbol, ' ')
        seed_info = input_string.split()
        try:
            seed_info = [int(i) for i in seed_info]
        except ValueError as error:
            error = str(error).split(':', 1)[1]
            self.show_warning(f'{error} is not a valid damage value.')
            return
        if len(seed_info) == 1:
            seed_info = seed_info[0]
            if seed_info > 0xffffffff:
                self.show_warning(
                    'Seed must be an integer between 0 and 4294967295')
                return
        elif len(seed_info) < 6:
            self.show_warning('Need at least 6 damage values.')
            return
        elif len(seed_info) > 6:
            self.show_warning(
                f'Submitted too many values: {len(seed_info)}')
            return
        try:
            self.rng_tracker = get_tracker(seed_info)
        except (InvalidDamageValueError,
                SeedNotFoundError) as error:
            self.show_warning(error)
            return

        print(f'Seed information: {seed_info}')

        self.destroy()

    def show_warning(self, text):
        if self.warning_label:
            self.warning_label.config(text=text)
        else:
            self.warning_label = tk.Label(self, text=text)
            self.warning_label.pack(fill='x')