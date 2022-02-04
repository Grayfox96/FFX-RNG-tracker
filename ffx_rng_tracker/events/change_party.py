from dataclasses import dataclass

from ..data.characters import Character
from .main import Event


@dataclass
class ChangeParty(Event):
    party_formation: list[Character]

    def __str__(self) -> str:
        character_names = [c.name for c in self.party_formation]
        return f'Party changed to: {", ".join(character_names)}'
