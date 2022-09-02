from dataclasses import dataclass, field

from ..data.constants import Character
from .main import Event


@dataclass
class ChangeParty(Event):
    party: list[Character]
    _old_party: list[Character] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._old_party = self.gamestate.party
        self.gamestate.party = self.party

    def __str__(self) -> str:
        return f'Party changed to: {", ".join(self.party)}'

    def rollback(self) -> None:
        self.gamestate.party = self._old_party
        return super().rollback()
