from dataclasses import dataclass

from ..data.characters import CharacterState
from ..data.constants import Stat
from ..data.monsters import MonsterState
from .main import Event


@dataclass
class ChangeStat(Event):
    target: CharacterState | MonsterState
    stat: Stat
    stat_value: int

    def __post_init__(self) -> None:
        if self.stat is Stat.CTB:
            self.target.ctb = self.stat_value
            self.stat_value = self.target.ctb
            self.gamestate.normalize_ctbs(self.gamestate.get_min_ctb())
            return
        self.stat_value = self._set_stat()

    def __str__(self) -> str:
        return (f'{self.target}\'s {self.stat} '
                f'changed to {self.stat_value}')

    def _set_stat(self) -> int:
        self.target.set_stat(self.stat, self.stat_value)
        return self.target.stats[self.stat]
