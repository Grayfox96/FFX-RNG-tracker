from dataclasses import dataclass

from ..data.actor import MonsterActor
from ..data.constants import MonsterSlot, Status
from ..data.monsters import Monster
from .main import Event


@dataclass
class MonsterSpawn(Event):
    monster: Monster
    slot: MonsterSlot
    ctb: int | None = None

    def __post_init__(self) -> None:
        self.new_monster = self._spawn_monster()
        self.ctb = self._calc_ctb()

    def __str__(self) -> str:
        return f'Spawn: {self.new_monster} with {self.ctb} CTB'

    def _spawn_monster(self) -> MonsterActor:
        actor = MonsterActor(self.monster, self.slot)
        if self.slot < len(self.gamestate.monster_party):
            self.gamestate.monster_party[self.slot] = actor
        else:
            self.gamestate.monster_party.append(actor)
        return actor

    def _calc_ctb(self) -> int:
        if self.ctb is not None:
            self.new_monster.ctb = self.ctb
            return self.new_monster.ctb
        last_actor = self.gamestate.last_actor
        if last_actor.last_action:
            last_actor_ctb_at_spawn = (last_actor.base_ctb
                                       * last_actor.last_action.rank)
        else:
            last_actor_ctb_at_spawn = 0
        if Status.HASTE in last_actor.statuses:
            last_actor_ctb_at_spawn //= 2
        elif Status.SLOW in last_actor.statuses:
            last_actor_ctb_at_spawn *= 2
        # calculate the ctb that passed between when the last action
        # was performed and when monsterspawn is called and then subtract it
        # from what the ctb should have been if the events were simultaneous
        ctb_to_subtract = last_actor_ctb_at_spawn - last_actor.ctb
        ctb = self.new_monster.base_ctb * 3 - ctb_to_subtract
        self.new_monster.ctb = ctb
        return self.new_monster.ctb
