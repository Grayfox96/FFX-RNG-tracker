from ..data.constants import EquipmentType
from ..ui_functions import get_encounter_predictions, get_equipment_types
from ..utils import treeview
from .base_widgets import BaseWidget


class SeedInfo(BaseWidget):
    """Widget that shows general information
    about the seed.
    """

    def make_input_widget(self) -> None:
        return

    def get_tags(self) -> dict[str, str]:
        return {'equipment': str(EquipmentType.ARMOR)}

    def get_default_input_text(self) -> str:
        return self.get_input()

    def get_input(self) -> str:
        data = []
        seed = self.gamestate.seed
        data.append(f'Seed number: {seed}')
        encounter_predictions = treeview(get_encounter_predictions(seed), 1)
        data.append('Encounters predictions:\n' + encounter_predictions)
        data.append(get_equipment_types(seed, 50, 2))
        return '\n\n'.join(data)

    def parse_input(self) -> None:
        self.print_output(self.get_input())
