from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..data.characters import CHARACTERS, CharacterState
from ..data.constants import BASE_COMPATIBILITY
from ..tracker import FFXRNGTracker


class GameState:
    """Keeps track of various state variables necessary
    to properly instantiate events.
    """

    def __init__(self, seed: int) -> None:
        self._rng_tracker = FFXRNGTracker(seed)
        self.events_sequence: list[Event] = []
        self.characters = self._get_characters()
        self.zone_encounters_counts: dict[str, int] = {}
        self._compatibility = BASE_COMPATIBILITY
        self.reset()

    def _get_characters(self) -> dict[str, CharacterState]:
        characters = {}
        for name, c in CHARACTERS.items():
            characters[name] = CharacterState(
                name=c.name,
                index=c.index,
                _default_stats=c._default_stats.copy(),
                elemental_affinities=c.elemental_affinities.copy(),
            )
        return characters

    def reset(self) -> None:
        self._rng_tracker.reset()
        self.events_sequence.clear()
        self.party = [CHARACTERS['tidus'], CHARACTERS['auron']]
        self.compatibility = BASE_COMPATIBILITY
        self.equipment_drops = 0
        self.encounters_count = 0
        self.random_encounters_count = 0
        self.zone_encounters_counts.clear()
        for character in self.characters.values():
            character.reset()

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
    _rng_rolls: dict[int, int] = field(
        default_factory=dict, init=False, repr=False)

    @abstractmethod
    def __str__(self) -> str:
        pass

    def _advance_rng(self, index: int) -> int:
        rng_rolls = self._rng_rolls.get(index, 0)
        self._rng_rolls[index] = rng_rolls + 1
        return self.gamestate._rng_tracker.advance_rng(index)

    def rollback(self) -> None:
        for index, rolls in self._rng_rolls.items():
            self.gamestate._rng_tracker._rng_current_positions[index] -= rolls
