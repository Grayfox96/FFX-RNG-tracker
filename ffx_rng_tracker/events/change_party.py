from dataclasses import dataclass

from ..data.constants import Character
from .main import Event


@dataclass
class ChangeParty(Event):
    party: list[Character]

    def __post_init__(self) -> None:
        self.old_party = self.gamestate.party
        self.gamestate.party = self.party

    def __str__(self) -> str:
        return f'Party: {', '.join(self.old_party)} -> {', '.join(self.party)}'
