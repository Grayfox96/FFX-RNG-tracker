from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ..main import get_tracker
from ..tracker import FFXRNGTracker


@dataclass
class Event(ABC):
    """Abstract base class for all events."""
    _rng_tracker: FFXRNGTracker = field(
        default_factory=get_tracker, init=False, repr=False)

    @abstractmethod
    def __str__(self) -> str:
        pass
