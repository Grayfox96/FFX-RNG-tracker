import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import font, simpledialog, ttk
from typing import Callable

from ..configs import Configs
from ..data.seeds import DAMAGE_VALUES_NEEDED, get_seed
from ..errors import InvalidDamageValueError, SeedNotFoundError
from ..events.gamestate import GameState
from ..events.main import Event
from ..events.parser import EventParser
from ..events.parsing import parse_roll


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

    def _add_h_scrollbar(self) -> None:
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

    def set(self, text: str) -> bool:
        """If the previous text and the new one are identical returns False,
        otherwise it replaces the previous text, scrolls back to the
        previous position and returns True.
        """
        # a newline character gets automatically added
        # so it needs to be removed to compare
        current_text = self.get('1.0', 'end')[:-1]
        if text == current_text:
            return False
        current_number_of_lines = len(current_text.split('\n'))
        last_line = self.index(f'@0,{self.winfo_height()}')
        line_index = int(last_line.split('.')[0])

        self.replace(1.0, 'end', text)

        # scroll vertically if the last line of the text was visible
        if line_index == current_number_of_lines and line_index > 1:
            self.yview_pickplace('end')
        return True


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


class ScrollableFrame(tk.Frame):
    """"""

    def __init__(self, parent, *args, **kwargs) -> None:
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

    def pack(self, *args, **kwargs) -> None:
        self.outer_frame.pack(*args, **kwargs)

    def grid(self, *args, **kwargs) -> None:
        self.outer_frame.grid(*args, **kwargs)


class BaseWidget(tk.Frame, ABC):
    """Abstract base class for all tkinter widgets."""

    def __init__(self, parent, seed: int, *args, **kwargs) -> None:
        self.gamestate = GameState(seed)
        self.parser = EventParser(self.gamestate)
        for name, function in self.get_parsing_functions().items():
            self.parser.register_parsing_function(name, function)
        self.font = font.Font(family='Courier New', size=Configs.font_size)
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.input_widget = self.make_input_widget()
        self.output_widget = self.make_output_widget()
        self.tags = self.get_tags()
        self.parse_input()

    def make_input_widget(self) -> BetterText:
        """Initializes input widget."""
        text = BetterText(
            self, font=self.font, width=40, undo=True, autoseparators=True,
            maxundo=-1)
        text.set(self.get_default_input_text())
        text.pack(fill='y', side='left')
        text.bind('<KeyRelease>', lambda _: self.parse_input())
        return text

    def make_output_widget(self) -> BetterText:
        """Initialize output widget."""
        text = BetterText(self, font=self.font, state='disabled', wrap='word')
        text.pack(expand=True, fill='both', side='right')

        for tag_name, (foreground, background) in Configs.colors.items():
            if foreground == '#000000':
                selectforeground = '#ffffff'
            else:
                selectforeground = foreground
            if background in ('#ffffff', '#333333'):
                selectbackground = '#007fff'
            else:
                selectbackground = background
            text.tag_configure(
                tag_name, foreground=foreground, background=background,
                selectforeground=selectforeground,
                selectbackground=selectbackground)
        text.tag_configure('wrap_margin', lmargin2='1c')
        return text

    def highlight_patterns(self) -> None:
        for text, tag, regexp in self.tags:
            self.output_widget.highlight_pattern(text, tag, regexp=regexp)

    def get_tags(self) -> list[tuple[str, str, bool]]:
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

    def get_parsing_functions(self) -> dict[str, Callable[..., Event]]:
        """Returns a dictionary with strings as keys
        and functions that accept a GameState and any number
        of strings as arguments and return events as values.
        """
        parsing_functions = {
            'roll': parse_roll,
            'waste': parse_roll,
            'advance': parse_roll,
        }
        return parsing_functions

    @abstractmethod
    def get_default_input_text(self) -> str:
        """Retrieve the default input text."""

    def get_input(self) -> str:
        """Get the input as a string."""
        return self.input_widget.get('1.0', 'end')

    @abstractmethod
    def parse_input(self) -> None:
        """Parse the input widget text send output to the output widget."""

    def print_output(self, text: str) -> None:
        """Overwrites the output widget content with the text, if the text
        is different than the current one it highlights keywords."""
        self.output_widget.config(state='normal')
        if self.output_widget.set(text):
            self.highlight_patterns()
        self.output_widget.config(state='disabled')


class DamageValuesDialogue(simpledialog.Dialog):
    """Input dialogue used to get damage values."""

    def __init__(self, *args, **kwargs):
        self.warning_label = False
        self.seed = None
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
        match seed_info:
            case []:
                return
            case [seed]:
                if not (0 <= seed <= 0xffffffff):
                    self.show_warning(
                        'Seed must be an integer between 0 and 4294967295')
                    return
            case _ if len(seed_info) < DAMAGE_VALUES_NEEDED:
                self.show_warning(
                    f'Need at least {DAMAGE_VALUES_NEEDED} damage values.')
                return
            case _:
                try:
                    seed = get_seed(seed_info)
                except (InvalidDamageValueError,
                        SeedNotFoundError) as error:
                    self.show_warning(error)
                    return

        self.seed = seed
        self.destroy()

    def show_warning(self, text):
        if self.warning_label:
            self.warning_label.config(text=text)
        else:
            self.warning_label = tk.Label(self, text=text)
            self.warning_label.pack(fill='x')
