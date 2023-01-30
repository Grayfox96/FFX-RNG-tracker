from dataclasses import dataclass

from ..data.constants import Character
from .main import Event


@dataclass
class Death(Event):
    character: Character

    def __post_init__(self) -> None:
        for _ in range(3):
            self._advance_rng(10)
        self._update_compatibility()

    def __str__(self) -> str:
        return f'Character death: {self.character}'

    def _update_compatibility(self) -> None:
        if self.character is Character.YOJIMBO:
            self.gamestate.compatibility -= 10
