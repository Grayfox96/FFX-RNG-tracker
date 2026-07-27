from dataclasses import dataclass

from ..data.actions import ACTIONS
from ..data.actor import CharacterActor
from ..data.constants import Status
from .main import Event


@dataclass
class Escape(Event):
    character: CharacterActor

    def __post_init__(self) -> None:
        self.gamestate.process_start_of_turn(self.character)
        self.escape = self._get_escape()
        self.ctb = self._get_ctb()
        self.gamestate.process_end_of_turn(self.character, ACTIONS['escape'])

    def __str__(self) -> str:
        string = f'{self.character} -> Escape [{self.ctb}]: '
        if self.escape:
            string += 'Succeeded'
        else:
            string += 'Failed'
        return string

    def _get_escape(self) -> bool:
        index = min(20 + self.character.index, 27)
        escape_roll = self._advance_rng(index) & 255
        escape = escape_roll < 191
        if escape:
            self.character.statuses[Status.EJECT] = 254
        return escape

    def _get_ctb(self) -> int:
        ctb = self.character.base_ctb
        if Status.HASTE in self.character.statuses:
            ctb = ctb // 2
        elif Status.SLOW in self.character.statuses:
            ctb = ctb * 2
        self.character.ctb += ctb
        return ctb
