import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from ..configs import Configs, UIWidgetConfigs
from ..data.seeds import DAMAGE_VALUES_NEEDED, get_seed
from ..errors import InvalidDamageValueError, SeedNotFoundError
from ..ui_functions import get_equipment_types, get_status_chance_table
from .output_widget import TkOutputWidget


class TkSeedInfo(tk.Frame):
    def __init__(self,
                 parent,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)

        self.inner_frame = tk.Frame(self)
        self.inner_frame.pack()

        damage_values_needed = DAMAGE_VALUES_NEEDED[Configs.game_version]
        text = (f'Input the first {damage_values_needed} damage values '
                'in this order: ')
        if damage_values_needed == 3:
            text += 'Auron1 Tidus Auron2\n'
        else:
            text += ('Auron1 Tidus1 A2 T2 A3 T3 A4 A5\n'
                     '(A4 and A5 are the first 2 Auron Attacks '
                     'vs Sinspawn Ammes)\n')
        text += 'Alternatively input a Seed Number to load that seed directly'
        self.info_label = tk.Label(self.inner_frame, text=text)
        self.info_label.pack()

        self.entry = tk.Entry(self.inner_frame)
        if Configs.seed is not None:
            self.entry.insert(0, str(Configs.seed))
        self.entry.pack(fill='x')
        self.entry.bind('<Return>', lambda _: self.validate_input())

        self.button = tk.Button(
            self.inner_frame, text='Submit', command=self.validate_input)
        self.button.place(relx=0.5, rely=1, anchor='s')
        self.reload_notes = ttk.Checkbutton(
            self.inner_frame, text='Reload notes', padding=5)
        self.reload_notes.pack(side='right')

        self.warning_label = tk.Label(self)

        self.output_widget = TkOutputWidget(self, wrap='none')
        for name in configs.tag_names:
            self.output_widget.register_tag(name)
        self.output_widget.pack(expand=True, fill='both')

        def callback_func(seed: int, reload_notes: bool) -> None:
            return

        self.callback_func = callback_func

    def register_callback(self,
                          callback_func: Callable[[int, bool], None],
                          ) -> None:
        self.callback_func = callback_func

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
            self.show_warning(f'{error} is not a valid damage value')
            return
        match seed_info:
            case []:
                self.show_warning('Input damage values or a Seed Number first')
                return
            case [seed]:
                if not (0 <= seed <= 0xffffffff):
                    self.show_warning(
                        'Seed must be an integer between 0 and 4294967295')
                    return
            case _:
                try:
                    seed = get_seed(
                        seed_info, Configs.continue_ps2_seed_search)
                except (InvalidDamageValueError,
                        SeedNotFoundError) as error:
                    self.show_warning(error)
                    return

        self.show_warning('')
        self.print_output(seed)
        reload_notes = 'selected' in self.reload_notes.state()
        self.callback_func(seed, reload_notes)

    def print_output(self, seed: int) -> None:
        data = [
            f'Seed Number: {seed}',
            get_equipment_types(seed, 50, 2),
            get_status_chance_table(seed, 99),
        ]
        output = '\n\n'.join(data)
        self.output_widget.print_output(output)

    def show_warning(self, text: str) -> None:
        if text:
            text = f'Error: {text}'
            self.warning_label.pack(fill='x', after=self.inner_frame)
        else:
            self.warning_label.forget()
        self.warning_label.config(text=text)
