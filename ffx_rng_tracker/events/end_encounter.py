from dataclasses import dataclass

from ..data.constants import Character, Status
from ..ui_functions import ctb_sorter
from .main import Event


@dataclass
class EndEncounter(Event):

    def __post_init__(self) -> None:
        self.ctbs_string = self._get_ctbs_string()
        self.hps = self._get_hps()
        self.monsters_hps = self._get_monsters_hps()
        self.gamestate.process_end_of_encounter()

    def __str__(self) -> str:
        hps = ' '.join([f'{c[:2]}[{hp}]' for c, hp in self.hps.items()])
        if not hps:
            hps = 'Characters at full HP'
        monsters_hps = ' '.join([f'{m}[{hp}]'
                                 for m, hp in self.monsters_hps.items()])
        if not monsters_hps:
            monsters_hps = 'Monsters at full HP'
        string = (f'End: CTBs: {self.ctbs_string}\n'
                  f'     Characters HPs: {hps}\n'
                  f'     Monsters HPs: {monsters_hps}'
                  )
        return string

    def _get_ctbs_string(self) -> str:
        characters = []
        for character, actor in self.gamestate.characters.items():
            if (character in self.gamestate.party
                    and Status.DEATH not in actor.statuses
                    and Status.EJECT not in actor.statuses):
                characters.append(actor)
        monsters = []
        for actor in self.gamestate.monster_party:
            if (Status.DEATH not in actor.statuses
                    and Status.EJECT not in actor.statuses):
                monsters.append(actor)
        return ctb_sorter(characters, monsters)

    def _get_hps(self) -> dict[Character, int]:
        hps = {}
        for character, actor in self.gamestate.characters.items():
            if actor.current_hp < actor.max_hp:
                hps[character] = actor.current_hp
        return hps

    def _get_monsters_hps(self) -> dict[str, int]:
        monsters_hps = {}
        for actor in self.gamestate.monster_party:
            monsters_hps[str(actor)] = actor.current_hp
        return monsters_hps
