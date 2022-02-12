from dataclasses import dataclass, field

from ..data.actions import Action
from ..data.characters import CHARACTERS, Character
from ..data.monsters import Monster
from .change_party import ChangeParty
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

    def _get_hit(self):
        # not implemented yet
        return True

    def _get_damage(self):
        # not implemented yet
        return 0, 0, False

    def _get_possible_targets(self) -> list[CHARACTERS]:
        formation = [CHARACTERS['tidus'], CHARACTERS['auron']]
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, ChangeParty):
                formation = event.party_formation
                break
        return formation

    def _get_targets(self):
        possible_targets = self._get_possible_targets()
        if len(possible_targets) <= 1:
            return possible_targets
        # not implemented yet
        # if action is aoe -> return all targets
        # if action is multihit -> advance rng5 for every hit
        target_rng = self._rng_tracker.advance_rng(4)
        target_index = target_rng % len(possible_targets)
        return [possible_targets[target_index]]
