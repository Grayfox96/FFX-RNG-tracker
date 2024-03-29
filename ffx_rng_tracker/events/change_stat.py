from dataclasses import dataclass

from ..data.actor import Actor
from ..data.constants import Character, Stat
from .main import Event


@dataclass
class ChangeStat(Event):
    target: Actor
    stat: Stat
    stat_value: int

    def __post_init__(self) -> None:
        self.old_stat_value = self.target.stats[self.stat]
        self.stat_value = self._set_stat()
        if (hasattr(self.target, 'character')
                and self.target.character is Character.YUNA):
            self.gamestate.calculate_aeon_stats()

    def __str__(self) -> str:
        string = (f'Stat: {self.target} | {self.stat} | '
                  f'{self.old_stat_value} -> {self.stat_value}')
        return string

    def _set_stat(self) -> int:
        self.target.set_stat(self.stat, self.stat_value)
        return self.target.stats[self.stat]
