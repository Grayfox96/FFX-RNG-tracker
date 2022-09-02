from dataclasses import dataclass, field

from ..data.constants import Character
from .main import Event


@dataclass
class Death(Event):
    dead_character: Character
    _old_compatibility: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        for _ in range(3):
            self._advance_rng(10)
        self._update_compatibility()

    def __str__(self) -> str:
        return f'Character death: {self.dead_character}'

    def _update_compatibility(self) -> None:
        self._old_compatibility = self.gamestate.compatibility
        if self.dead_character is Character.YOJIMBO:
            self.gamestate.compatibility = self.gamestate.compatibility - 10

    def rollback(self) -> None:
        self.gamestate.compatibility = self._old_compatibility
        return super().rollback()
