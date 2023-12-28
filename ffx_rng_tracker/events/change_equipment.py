from dataclasses import dataclass

from ..data.constants import EquipmentType
from ..data.equipment import Equipment
from .main import Event


@dataclass
class ChangeEquipment(Event):
    equipment: Equipment

    def __post_init__(self) -> None:
        self._change_equipment()

    def __str__(self) -> str:
        string = (f'{self.equipment.owner}\'s {self.equipment.type_} '
                  f'changed to {self.equipment}')
        return string

    def _change_equipment(self) -> None:
        actor = self.gamestate.characters[self.equipment.owner]
        if self.equipment.type_ is EquipmentType.WEAPON:
            actor.weapon = self.equipment
        elif self.equipment.type_ is EquipmentType.ARMOR:
            actor.armor = self.equipment
