from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..data.characters import CHARACTERS
from ..data.constants import BASE_COMPATIBILITY
from ..tracker import FFXRNGTracker


class GameState:

    def __init__(self, seed: int) -> None:
        self._rng_tracker = FFXRNGTracker(seed)
        self.events_sequence: list[Event] = []
        self.zone_encounters_counts: dict[str, int] = {}
        self._compatibility = BASE_COMPATIBILITY
        self.reset()

    def reset(self) -> None:
        self._rng_tracker.reset()
        self.events_sequence.clear()
        self.party = [CHARACTERS['tidus'], CHARACTERS['auron']]
        self.compatibility = BASE_COMPATIBILITY
        self.equipment_drops = 0
        self.encounters_count = 0
        self.random_encounters_count = 0
        self.zone_encounters_counts.clear()
        for character in CHARACTERS.values():
            character.reset_stats()

    @property
    def compatibility(self) -> int:
        return self._compatibility

    @compatibility.setter
    def compatibility(self, value: int) -> None:
        self._compatibility = max(min(value, 255), 0)

    @property
    def seed(self) -> int:
        return self._rng_tracker.seed


@dataclass
class Event(ABC):
    """Abstract base class for all events."""
    gamestate: GameState

    @abstractmethod
    def __str__(self) -> str:
        pass

    def _advance_rng(self, index: int) -> int:
        return self.gamestate._rng_tracker.advance_rng(index)
