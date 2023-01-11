from dataclasses import dataclass, field

from ..data.constants import MonsterSlot
from ..data.monsters import Monster, MonsterState
from .main import Event


@dataclass
class MonsterSpawn(Event):
    monster: Monster
    slot: MonsterSlot
    forced_ctb: int = 0
    _old_monster: MonsterState | None = field(init=False, repr=False)
    _new_monster: MonsterState = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._new_monster = self._spawn_monster()

    def __str__(self) -> str:
        string = (f'Spawned monster {self._new_monster} '
                  f'with {self._new_monster.ctb} CTB')
        return string

    def _spawn_monster(self) -> MonsterState:
        monster = MonsterState(self.monster, self.slot)
        if self.forced_ctb:
            monster.ctb = self.forced_ctb
        else:
            monster.ctb = monster.base_ctb * 3
        if self.slot < len(self.gamestate.monster_party):
            self._old_monster = self.gamestate.monster_party[self.slot]
            self.gamestate.monster_party[self.slot] = monster
        else:
            self._old_monster = None
            self.gamestate.monster_party.append(monster)
        return monster

    def rollback(self) -> None:
        if self._old_monster is not None:
            self.gamestate.monster_party[self.slot] = self._old_monster
        else:
            self.gamestate.monster_party.pop()
        return super().rollback()
