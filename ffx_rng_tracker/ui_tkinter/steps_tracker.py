from tkinter import ttk

from ..configs import UIWidgetConfigs
from ..data.encounters import get_steps_notes
from ..events.parser import EventParser
from ..ui_abstract.steps_tracker import StepsTracker
from .base_widgets import TkConfirmPopup, TkWarningPopup
from .encounters_tracker import TkEncountersInputWidget
from .input_widget import TkSearchBarWidget
from .output_widget import TkOutputWidget


class TkStepsInputWidget(TkEncountersInputWidget):

    def get_input(self) -> str:
        current_zone = self.sliders.current_zone.get()
        input_data = []
        if 'selected' not in self.padding_button.state():
            input_data.append('/nopadding\n///')
        for slider in self.sliders:
            steps = slider.value
            if current_zone == slider.zone_index:
                input_data.append('///')
            input_data.append(f'walk {slider.data.zone} {steps} '
                              f'{slider.data.continue_previous_zone}')
        return '\n'.join(input_data)


class TkStepsTracker(ttk.Frame):

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 *args,
                 **kwargs,
                 ) -> None:
        super().__init__(parent, *args, **kwargs)
        frame = ttk.Frame(self)
        frame.pack(fill='y', side='left')

        search_bar = TkSearchBarWidget(frame)
        search_bar.pack(fill='x')

        input_widget = TkStepsInputWidget(frame)
        encounters = get_steps_notes(
            StepsTracker.notes_file, parser.gamestate.seed)
        for encounter in encounters:
            input_widget.sliders.add_slider(encounter)
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
