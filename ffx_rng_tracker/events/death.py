from dataclasses import dataclass

from ..data.characters import CHARACTERS, Character
from .main import Event


@dataclass
class Death(Event):
    dead_character: Character

    def __post_init__(self) -> None:
        self._advance_rng()
        if self.dead_character == CHARACTERS['yojimbo']:
            self._update_compatibility()

    def __str__(self) -> str:
        return f'Character death: {self.dead_character}'

    def _advance_rng(self) -> None:
        for _ in range(3):
            self._rng_tracker.advance_rng(10)

    def _update_compatibility(self) -> None:
        compatibility = self._rng_tracker.compatibility
        self._rng_tracker.compatibility = max(compatibility - 10, 0)
