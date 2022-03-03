from dataclasses import dataclass, field

from ..data.actions import Action
from ..data.characters import Character
from ..data.monsters import Monster
from .main import Event


@dataclass
class MonsterAction(Event):
    monster: Monster
    action: Action
    slot: int
    hit: bool = field(init=False, repr=False)
    damage: int = field(init=False, repr=False)
    damage_rng: int = field(init=False, repr=False)
    crit: bool = field(init=False, repr=False)
    targets: list[Character] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.hit = self._get_hit()
        self.damage, self.damage_rng, self.crit = self._get_damage()
        self.targets = self._get_targets()

    def __str__(self) -> str:
        targets = ', '.join([t.name for t in self.targets])
        return f'{self.monster.name} -> {targets}'

    def _get_hit(self) -> bool:
        # not implemented yet
        return True

    def _get_damage(self) -> tuple[int, int, bool]:
        # not implemented yet
        return 0, 0, False

    def _get_possible_targets(self) -> list[Character]:
        return self.gamestate.party[:3]

    def _get_targets(self) -> list[Character]:
        possible_targets = self._get_possible_targets()
        if len(possible_targets) <= 1:
            return possible_targets
        # not implemented yet
        # if action is aoe -> return all targets
        # if action is multihit -> advance rng5 for every hit
        target_rng = self._advance_rng(4)
        target_index = target_rng % len(possible_targets)
        return [possible_targets[target_index]]
