from dataclasses import dataclass, field

from ..data.characters import CharacterState
from ..data.constants import ICV_BASE, Stat, Status
from .main import Event


@dataclass
class Escape(Event):
    character: CharacterState
    escape: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.escape = self._get_escape()
        self.ctb = self._get_ctb()

    def __str__(self) -> str:
        string = f'{self.character}: Escape [{self.ctb}] ->'
        if self.escape:
            string += ' Succeeded'
        else:
            string += ' Failed'
        return string

    def _get_escape(self) -> bool:
        index = 20 + self.character.index
        escape_roll = self._advance_rng(index) & 255
        escape = escape_roll < 191
        if escape:
            self.character.statuses.add(Status.EJECT)
        return escape

    def _get_ctb(self) -> int:
        ctb_base = ICV_BASE[self.character.stats[Stat.AGILITY]]
        return ctb_base

    def rollback(self) -> None:
        self.character.statuses.discard(Status.EJECT)
        return super().rollback()
