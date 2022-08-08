from dataclasses import dataclass, field

from ..data.constants import EquipmentType
from ..data.equipment import Equipment
from .main import Event


@dataclass
class ChangeEquipment(Event):
    equipment: Equipment
    _old_equipment: Equipment = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._old_equipment = self._swap_old_equipment()

    def __str__(self) -> str:
        string = (f'{self.equipment.owner}\'s {self.equipment.type_} '
                  f'changed to {self.equipment}')
        return string

    def _swap_old_equipment(self) -> Equipment:
        character = self.gamestate.characters[self.equipment.owner]
        if self.equipment.type_ is EquipmentType.WEAPON:
            old_equipment = character.weapon
            character.weapon = self.equipment
        elif self.equipment.type_ is EquipmentType.ARMOR:
            old_equipment = character.armor
            character.armor = self.equipment
        return old_equipment

    def rollback(self) -> None:
        character = self.gamestate.characters[self.equipment.owner]
        if self.equipment.type_ is EquipmentType.WEAPON:
            character.weapon = self._old_equipment
        elif self.equipment.type_ is EquipmentType.ARMOR:
            character.armor = self._old_equipment
        return super().rollback()
