from dataclasses import dataclass, field

from ..data.constants import TEMPORARY_STATS, Character, Stat, Status
from ..data.monsters import MonsterState
from .main import Event


@dataclass
class EndEncounter(Event):
    _statuses: dict[Character, set[Status]] = field(
        default_factory=dict, init=False, repr=False)
    _hps: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)
    _old_monster_party: list[MonsterState] = field(
        default_factory=list, init=False, repr=False)
    _temp_stats: dict[Character, dict[Stat, int]] = field(
        default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self._cleanup()

    def __str__(self) -> str:
        hps = ', '.join([f'{c} {hp}' for c, hp in self._hps.items()])
        if not hps:
            hps = 'everyone is at max HP'
        dead_monsters = ', '.join([f'{m}' for m in self._old_monster_party
                                   if m.dead])
        if not dead_monsters:
            dead_monsters = 'none'
        return f'Characters hps: {hps} | Dead monsters: {dead_monsters}'

    def _cleanup(self) -> None:
        for character, state in self.gamestate.characters.items():
            if Status.DEATH in state.statuses:
                state.current_hp = 1
            if state.current_hp < state.max_hp:
                self._hps[character] = state.current_hp
            self._statuses[character] = state.statuses.copy()
            state.statuses.clear()
            self._temp_stats[character] = {}
            for stat in TEMPORARY_STATS:
                self._temp_stats[character][stat] = state.stats[stat]
                state.stats[stat] = 0
        self._old_monster_party = self.gamestate.monster_party
        self.gamestate.monster_party = []

    def rollback(self) -> None:
        for character, statuses in self._statuses.items():
            self.gamestate.characters[character].statuses = statuses
        for character, hp in self._hps.items():
            self.gamestate.characters[character].current_hp = hp
        for character, stats in self._temp_stats.items():
            for stat, value in stats.items():
                self.gamestate.characters[character].stats[stat] = value
        return super().rollback()
