import tkinter as tk

from ..configs import UIWidgetConfigs
from ..data.encounters import StepsData, get_steps_notes
from ..events.parser import EventParser
from ..ui_abstract.steps_tracker import StepsTracker
from .base_widgets import TkConfirmPopup, TkWarningPopup
from .encounters_tracker import TkEncountersInputWidget
from .input_widget import TkSearchBarWidget
from .output_widget import TkOutputWidget


class TkStepsInputWidget(TkEncountersInputWidget):

    def get_input(self) -> str:
        current_zone = self.current_zone.get()
        input_data = []
        if 'selected' not in self.padding_button.state():
            input_data.append('/nopadding\n///')
        self.encounters: list[StepsData]
        for encounter in self.encounters:
            steps = self.sliders[encounter.label].get()
            if current_zone == encounter.label:
                input_data.append('///')
            input_data.append(f'walk {encounter.zone} {steps} '
                              f'{encounter.continue_previous_zone}')
        return '\n'.join(input_data)


class TkStepsTracker(tk.Frame):

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)
        frame = tk.Frame(self)
        frame.pack(fill='y', side='left')

        search_bar = TkSearchBarWidget(frame)
        search_bar.pack(fill='x')

        input_widget = TkStepsInputWidget(frame)
        encounters = get_steps_notes(
            StepsTracker.notes_file, parser.gamestate.seed)
        input_widget.encounters = encounters
        for encounter in encounters:
            input_widget.add_slider(
                encounter.label, encounter.min,
                encounter.default, encounter.max)
        input_widget.pack(expand=True, fill='y')

        output_widget = TkOutputWidget(self, wrap='none')
        output_widget.pack(expand=True, fill='both', side='right')
        output_widget.text.bind(
            '<Control-s>', lambda _: self.tracker.save_input_data())

        self.tracker = StepsTracker(
            configs=configs,
            parser=parser,
            input_widget=input_widget,
            output_widget=output_widget,
            search_bar=search_bar,
            warning_popup=TkWarningPopup(),
            confirmation_popup=TkConfirmPopup(),
            )
        self.tracker.callback()
