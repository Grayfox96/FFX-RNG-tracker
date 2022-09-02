from dataclasses import dataclass, field

from ..data.constants import Character, Status
from .main import Event


@dataclass
class EndEncounter(Event):
    _statuses: dict[Character, set[Status]] = field(
        default_factory=dict, init=False, repr=False)
    _hps: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._cleanup()

    def __str__(self) -> str:
        hps = [f'{c} {hp}' for c, hp in self._hps.items()]
        return f'Characters hps: {", ".join(hps)}'

    def _cleanup(self) -> None:
        for character, state in self.gamestate.characters.items():
            if Status.DEATH in state.statuses:
                state.current_hp = 1
            if state.current_hp < state.max_hp:
                self._hps[character] = state.current_hp
            self._statuses[character] = state.statuses.copy()
            state.statuses.clear()

    def rollback(self) -> None:
        for character, statuses in self._statuses.items():
            self.gamestate.characters[character].statuses = statuses
        for character, hp in self._hps.items():
            self.gamestate.characters[character].current_hp = hp
        return super().rollback()
