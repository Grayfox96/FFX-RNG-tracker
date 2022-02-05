from ..data.constants import EquipmentType
from ..ui_functions import get_encounter_predictions, get_equipment_types
from ..utils import treeview
from .base_widgets import BaseWidget


class SeedInfo(BaseWidget):
    """Widget that shows general information
    about the seed.
    """

    def make_input_widget(self):
        return

    def get_input(self):
        data = []
        data.append(f'Seed number: {self.rng_tracker.seed}')
        encounter_predictions = treeview(get_encounter_predictions(), 1)
        data.append('Encounters predictions:\n' + encounter_predictions)
        data.append(get_equipment_types(50, 2))
        return '\n\n'.join(data)

    def set_tags(self) -> list[tuple[str, str, bool]]:
        return [(EquipmentType.ARMOR, 'equipment', False)]

    def print_output(self):
        input = self.get_input()
        self.output_widget.config(state='normal')
        self.output_widget.insert('end', input)
        self.highlight_patterns()
        self.output_widget.config(state='disabled')
