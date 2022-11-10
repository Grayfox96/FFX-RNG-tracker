from dataclasses import dataclass, field

from ..data.characters import CharacterState
from ..data.constants import Autoability, Status
from .main import Event


@dataclass
class Escape(Event):
    character: CharacterState
    escape: bool = field(init=False, repr=False)
    _old_ctb: int = field(init=False, repr=False)

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
            self.character.statuses.add(Status.ESCAPE)
        return escape

    def _get_ctb(self) -> int:
        self._old_ctb = self.character.ctb
        ctb = self.character.base_ctb
        if (Status.HASTE in self.character.statuses
                or Autoability.AUTO_HASTE in self.character.autoabilities
                or (Autoability.SOS_HASTE in self.character.autoabilities
                    and self.character.in_crit)):
            ctb = ctb // 2
        elif Status.SLOW in self.character.statuses:
            ctb = ctb * 2
        self.character.ctb += ctb
        return ctb

    def rollback(self) -> None:
        self.character.statuses.discard(Status.ESCAPE)
        self.character.ctb = self._old_ctb
        return super().rollback()
