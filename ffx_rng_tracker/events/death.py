from dataclasses import dataclass

from ..data.constants import Character
from .main import Event


@dataclass
class Death(Event):
    character: Character
    comment: str

    def __post_init__(self) -> None:
        for _ in range(3):
            self._advance_rng(10)
        self._update_compatibility()

    def __str__(self) -> str:
        string = f'Character death: {self.character}'
        if self.comment:
            string += f' ({self.comment})'
        return string

    def _update_compatibility(self) -> None:
        if self.character is Character.YOJIMBO:
            self.gamestate.compatibility -= 10
