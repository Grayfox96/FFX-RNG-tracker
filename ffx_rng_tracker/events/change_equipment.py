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
        string = (f'Equipment: {self.equipment.owner} | '
                  f'{self.equipment.type_} | '
                  f'{self.old_equipment.name} '
                  f'[{self.old_equipment.abilities_string}] -> '
                  f'{self.equipment.name} '
                  f'[{self.equipment.abilities_string}]'
                  )
        return string

    def _change_equipment(self) -> None:
        actor = self.gamestate.characters[self.equipment.owner]
        if self.equipment.type_ is EquipmentType.WEAPON:
            self.old_equipment = actor.weapon
            actor.weapon = self.equipment
        elif self.equipment.type_ is EquipmentType.ARMOR:
            self.old_equipment = actor.armor
            actor.armor = self.equipment
