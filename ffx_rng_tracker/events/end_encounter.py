from dataclasses import dataclass, field

from ..data.constants import Buff, Character, Status
from ..data.monsters import MonsterState
from ..ui_functions import ctb_sorter
from .main import Event


@dataclass
class EndEncounter(Event):
    _statuses: dict[Character, set[Status]] = field(
        default_factory=dict, init=False, repr=False)
    _hps: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)
    _old_monster_party: list[MonsterState] = field(
        default_factory=list, init=False, repr=False)
    _buffs: dict[Character, dict[Buff, int]] = field(
        default_factory=dict, init=False, repr=False)
    _old_characters_ctbs: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)
    _old_monsters_ctbs: list[int] = field(
        default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.ctbs_string = self._get_ctbs_string()
        self._cleanup()

    def __str__(self) -> str:
        hps = ' '.join([f'{c[:2]:2}[{hp}]' for c, hp in self._hps.items()])
        if not hps:
            hps = 'Characters at full HP'
        monsters_hps = ' '.join([f'{m.monster}[{m.current_hp}]'
                                 for m in self._old_monster_party])
        if not monsters_hps:
            monsters_hps = 'Monsters at full HP'
        string = (f'CTBs: {self.ctbs_string} | '
                  f'Characters HPs: {hps} | '
                  f'Monsters HPs: {monsters_hps}')
        return string

    def _get_ctbs_string(self) -> str:
        characters = []
        for c, cs in self.gamestate.characters.items():
            if c in self.gamestate.party and not cs.dead and not cs.inactive:
                characters.append(cs)
        monsters = []
        for m in self.gamestate.monster_party:
            if not m.dead:
                monsters.append(m)
        return ctb_sorter(characters, monsters)

    def _cleanup(self) -> None:
        for character, state in self.gamestate.characters.items():
            if state.current_hp < state.max_hp:
                self._hps[character] = state.current_hp
            if Status.DEATH in state.statuses:
                state.current_hp = 1
            if character in self.gamestate.party:
                self._old_characters_ctbs[character] = state.ctb
            state.ctb = 0
            self._statuses[character] = state.statuses.copy()
            state.statuses.clear()
            self._buffs[character] = state.buffs.copy()
            for buff in state.buffs:
                state.buffs[buff] = 0
        for m in self.gamestate.monster_party:
            self._old_monsters_ctbs.append(m.ctb)
        self._old_monster_party = self.gamestate.monster_party
        self.gamestate.monster_party = []

    def rollback(self) -> None:
        for character, statuses in self._statuses.items():
            self.gamestate.characters[character].statuses = statuses
        for character, hp in self._hps.items():
            self.gamestate.characters[character].current_hp = hp
        for character, buffs in self._buffs.items():
            self.gamestate.characters[character].buffs = buffs.copy()
        for character, ctb in self._old_characters_ctbs.items():
            self.gamestate.characters[character].ctb = ctb
        return super().rollback()
