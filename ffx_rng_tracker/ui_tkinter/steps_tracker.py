from typing import Literal

from ..configs import UIWidgetConfigs
from ..data.encounters import StepsData, get_steps_notes
from ..events.parser import EventParser
from ..ui_abstract.steps_tracker import StepsTracker
from .encounters_tracker import EncounterSliders, TkEncountersInputWidget
from .tktracker import TkTracker


class TkStepsInputWidget(TkEncountersInputWidget):
    sliders: EncounterSliders[StepsData]

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


class TkStepsTracker(TkTracker):
    tracker_type = StepsTracker
    input_widget_type = TkStepsInputWidget

    def __init__(self,
                 parent,
                 parser: EventParser,
                 configs: UIWidgetConfigs,
                 orient: Literal['vertical', 'horizontal'] = 'horizontal',
                 ) -> None:
        super().__init__(parent, parser, configs, orient)
        self.input_widget: TkStepsInputWidget
        self.output_widget.text.config(wrap='none')
        self.output_widget.add_h_scrollbar()
        encounters = get_steps_notes(
            self.tracker.notes_file, parser.gamestate.seed)
        for encounter in encounters:
            self.input_widget.sliders.add_slider(encounter)
