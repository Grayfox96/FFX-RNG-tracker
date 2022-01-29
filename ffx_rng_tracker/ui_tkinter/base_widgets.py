import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import font, simpledialog, ttk
from typing import List, Tuple, Union

from ..configs import Configs
from ..errors import InvalidDamageValueError, SeedNotFoundError
from ..main import get_tracker


class BetterText(tk.Text):
    """Upgraded Text widget with an highlight_pattern
    method, a set method and with a vertical scrollbar
    and an optional horizontal scrollbar.
    """

    def __init__(self, parent, *args,  **kwargs) -> None:
        self.frame = tk.Frame(parent)
        self.v_scrollbar = tk.Scrollbar(self.frame)
        self.v_scrollbar.grid(row=0, column=1, sticky='ns')
        kwargs['yscrollcommand'] = self.v_scrollbar.set
        super().__init__(self.frame, *args, **kwargs)
        self.grid(row=0, column=0, sticky='nsew')
        self.v_scrollbar.configure(command=self.yview)
        if kwargs.get('wrap') == 'none':
            self._add_h_scrollbar()

        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self._override_geometry_managers()

    def _override_geometry_managers(self) -> None:
        """Override the geometry managers methods with the ones
        from the frame."""
        text_meths = vars(tk.Text).keys()
        methods = (vars(tk.Pack).keys()
                   | vars(tk.Grid).keys()
                   | vars(tk.Place).keys())
        methods = methods.difference(text_meths)

        for m in methods:
            if m[0] != '_' and m != 'config' and m != 'configure':
                setattr(self, m, getattr(self.frame, m))

    def _add_h_scrollbar(self):
        self.h_scrollbar = tk.Scrollbar(self.frame, orient='horizontal')
        self.h_scrollbar.grid(row=1, column=0, sticky='ew')
        self.configure(xscrollcommand=self.h_scrollbar.set)
        self.h_scrollbar.configure(command=self.xview)

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
        # get the index of the first and last visible lines
        first_line = self.index('@0,0')
        last_line = self.index(f'@0,{self.winfo_height()}')
        first_line_index = int(first_line.split('.')[0])
        last_line_index = int(last_line.split('.')[0])
        current_number_of_lines = len(current_text.split('\n'))
        new_number_of_lines = len(text)
        if (last_line_index == current_number_of_lines
                or first_line_index > new_number_of_lines):
            scroll_to_end = True
        else:
            scroll_to_end = False

        # overwrite the content
        self.delete(1.0, 'end')
        self.insert(1.0, text)

        if scroll_to_end and last_line_index > 1:
            self.see(last_line)
        else:
            self.see(first_line)
            _, first_line_y, *_ = self.dlineinfo(first_line)
            self.yview_scroll(first_line_y, 'pixels')


class BetterSpinbox(ttk.Spinbox):
    """Upgraded Spinbox widget with a set method
    and readonly by default.
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.set(0)

    def set(self, text: Union[str, int]) -> None:
        """Set the spinbox content."""
        self.config(state='normal')
        self.delete(0, 'end')
        self.insert(0, text)
        self.config(state='readonly')


class ScrollableFrame(tk.Frame):
    """"""

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        self.outer_frame = tk.Frame(parent)
        canvas = tk.Canvas(self.outer_frame, width=280)
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar = tk.Scrollbar(
            self.outer_frame, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.config(yscrollcommand=scrollbar.set)
        super().__init__(canvas, *args, **kwargs)
        super().pack(fill='both', expand=True)
        self.bind(
            '<Configure>',
            lambda _: canvas.config(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self, anchor='nw')
        # when the mouse enters the canvas it binds the mousewheel to scroll
        canvas.bind(
            '<Enter>',
            lambda _: canvas.bind_all(
                '<MouseWheel>',
                lambda e: canvas.yview_scroll(
                    int(-1 * (e.delta / 120)), 'units')))
        # when the mouse leaves the canvas it unbinds the mousewheel
        canvas.bind('<Leave>', lambda _: canvas.unbind_all('<MouseWheel>'))

    def pack(self, *args, **kwargs):
        self.outer_frame.pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        self.outer_frame.grid(*args, **kwargs)


class BaseWidget(tk.Frame, ABC):
    """Abstract base class for all tkinter widgets."""

    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        self.font = font.Font(family='Courier New', size=Configs.font_size)
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.rng_tracker = get_tracker()
        self.input_widget = self.make_input_widget()
        self.output_widget = self.make_output_widget()
        self.tags = self.set_tags()
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

        for tag_name, (foreground, background) in Configs.colors.items():
            if background in ('#ffffff', '#333333'):
                selectbackground = '#007fff'
            else:
                selectbackground = background
            text.tag_configure(
                tag_name, foreground=foreground, background=background,
                selectforeground=foreground, selectbackground=selectbackground)
        text.tag_configure('wrap_margin', lmargin2='1c')
        return text

    def highlight_patterns(self) -> None:
        for text, tag, regexp in self.tags:
            self.output_widget.highlight_pattern(text, tag, regexp=regexp)

    def set_tags(self) -> List[Tuple[str, str, bool]]:
        """Setup tags to be used by highlight_patterns."""
        error_messages = (
            'Invalid', 'No event called', 'Usage:', ' named ',
            'requires a target', ' advance rng ',
        )
        tags = [
            ('^Advanced rng.+$', 'advance rng', True),
            (f'^.*({"|".join(error_messages)}).+$', 'error', True),
            ('^.+$', 'wrap_margin', True),
        ]
        return tags

    @abstractmethod
    def get_input(self) -> None:
        """Parse the input widget text and add events to the tracker."""

    @abstractmethod
    def print_output(self) -> None:
        """Get information from the events sequence, highlight keywords."""


class DamageValuesDialogue(simpledialog.Dialog):
    """Input dialogue used to get damage values."""

    def __init__(self, *args, **kwargs):
        self.warning_label = False
        self.rng_tracker = None
        super().__init__(*args, **kwargs)

    def body(self, parent: tk.Tk):
        self.parent = parent
        text = 'Damage values (Auron1 Tidus1 A2 T2 A3 T3)'
        if Configs.ps2:
            text = text[:-1] + ' A4 A5)'
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
        for symbol in (',', '-', '/', '\\', '.'):
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
            if not (0 <= seed_info <= 0xffffffff):
                self.show_warning(
                    'Seed must be an integer between 0 and 4294967295')
                return
        elif len(seed_info) < 8 and Configs.ps2:
            self.show_warning('Need at least 8 damage values.')
            return
        elif len(seed_info) < 6:
            self.show_warning('Need at least 6 damage values.')
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
