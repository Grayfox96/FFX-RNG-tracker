from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..gamestate import GameState


@dataclass
class Event(ABC):
    """Abstract base class for all events."""
    gamestate: GameState

    @abstractmethod
    def __str__(self) -> str:
        pass

    def _advance_rng(self, index: int) -> int:
        return self.gamestate._rng_tracker.advance_rng(index)
