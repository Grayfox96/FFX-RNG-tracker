from dataclasses import dataclass

from ..data.constants import MonsterSlot
from ..data.monsters import Monster, MonsterState
from .main import Event


@dataclass
class MonsterSpawn(Event):
    monster: Monster
    slot: MonsterSlot
    ctb: int = 0

    def __post_init__(self) -> None:
        self.new_monster = self._spawn_monster()

    def __str__(self) -> str:
        string = (f'Spawned monster {self.new_monster} '
                  f'with {self.ctb} CTB')
        return string

    def _spawn_monster(self) -> MonsterState:
        monster = MonsterState(self.monster, self.slot)
        if self.ctb:
            monster.ctb = self.ctb
        else:
            ctb = monster.base_ctb * 3
            monster.ctb = ctb
            self.ctb = ctb
        if self.slot < len(self.gamestate.monster_party):
            self.gamestate.monster_party[self.slot] = monster
        else:
            self.gamestate.monster_party.append(monster)
        return monster
