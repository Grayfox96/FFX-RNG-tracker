from dataclasses import dataclass

from ..data.constants import (ICV_VARIANCE, Autoability, Character,
                              EncounterCondition, MonsterSlot, Stat, Status)
from ..data.encounter_formations import (BOSSES, FORMATIONS, SIMULATIONS,
                                         ZONES, Formation)
from ..data.monsters import MonsterState
from ..ui_functions import ctb_sorter
from .main import Event


@dataclass
class Encounter(Event):
    name: str

    def __post_init__(self) -> None:
        self.gamestate.process_start_of_encounter()
        self.formation = self._get_formation()
        self._update_current_monster_formation()
        self.condition = self._get_condition()
        self.index = self._get_index()
        self._duplicate_monsters_rng_advances()
        self.party_icvs = self._get_party_icvs()
        self.monsters_icvs = self._get_monsters_icvs()
        self.icvs_string = self._get_icvs_string()
        self.gamestate.normalize_ctbs()

    def __str__(self) -> str:
        name = FORMATIONS[self.name].name
        string = (f'Encounter {self.index:3} - {name}: {self.formation} '
                  f'{self.condition} {self.icvs_string}')
        return string

    def _get_index(self) -> int:
        self.gamestate.encounters_count += 1
        return self.gamestate.encounters_count

    def _get_formation(self) -> Formation:
        return BOSSES[self.name].formation

    def _update_current_monster_formation(self) -> None:
        for monster, slot in zip(self.formation.monsters, MonsterSlot):
            self.gamestate.monster_party.append(MonsterState(monster, slot))

    def _get_condition(self) -> EncounterCondition:
        condition_rng = self._advance_rng(1) & 255
        if self.formation.forced_condition is not None:
            return self.formation.forced_condition
        for character in self.gamestate.party:
            character_state = self.gamestate.characters[character]
            if Autoability.INITIATIVE in character_state.autoabilities:
                condition_rng -= 33
                break
        if condition_rng < 32:
            return EncounterCondition.PREEMPTIVE
        elif condition_rng < 255 - 32:
            return EncounterCondition.NORMAL
        else:
            return EncounterCondition.AMBUSH

    def _duplicate_monsters_rng_advances(self) -> None:
        monsters = self.formation.monsters
        for index, monster in enumerate(monsters):
            count = monsters.count(monster)
            if count > 1:
                if monsters.index(monster) == index:
                    for _ in range(count):
                        self._advance_rng(28 + index)
                self._advance_rng(28 + index)

    def _get_party_icvs(self) -> dict[str, int]:
        icvs = {}
        if self.condition is EncounterCondition.PREEMPTIVE:
            for character in self.gamestate.party:
                icvs[character] = 0
                self.gamestate.characters[character].ctb = 0
        elif self.condition is EncounterCondition.AMBUSH:
            for character, state in self.gamestate.characters.items():
                if character not in self.gamestate.party:
                    continue
                icv = state.base_ctb * 3
                icvs[character] = icv
                state.ctb = icv
        else:
            for character, state in self.gamestate.characters.items():
                if character is Character.UNKNOWN:
                    continue
                index = min(20 + state.index, 27)
                if character not in self.gamestate.party:
                    self._advance_rng(index)
                    continue
                variance_rng = self._advance_rng(index)
                variance = ICV_VARIANCE[state.stats[Stat.AGILITY]] + 1
                variance = variance_rng % variance
                base = state.base_ctb * 3
                icvs[character] = base - variance
                state.ctb = base - variance
        for character in icvs:
            state = self.gamestate.characters[character]
            if Autoability.FIRST_STRIKE in state.autoabilities:
                icvs[character] = 0
                state.ctb = 0
            elif Status.HASTE in state.statuses:
                icv = icvs[character] // 2
                icvs[character] = icv
                state.ctb = icv
        return icvs

    def _get_monsters_icvs(self) -> list[int]:
        icvs = []
        if self.condition is EncounterCondition.PREEMPTIVE:
            for m in self.gamestate.monster_party:
                icv = m.base_ctb * 3
                icvs.append(icv)
                m.ctb = icv
        elif self.condition is EncounterCondition.AMBUSH:
            for m in self.gamestate.monster_party:
                icvs.append(0)
                m.ctb = 0
        else:
            for m in self.gamestate.monster_party:
                base = m.base_ctb * 3 * 100
                index = min(m.slot + 28, 35)
                variance_rng = self._advance_rng(index)
                variance = 100 - (variance_rng % 11)
                icvs.append(base // variance)
                m.ctb = base // variance
            # empty monster party slots still advance rng
            for index in range(28 + len(self.formation.monsters), 36):
                self._advance_rng(index)
        return icvs

    def _get_icvs_string(self) -> str:
        characters = [cs for c, cs in self.gamestate.characters.items()
                      if c in self.gamestate.party]
        monsters = self.gamestate.monster_party
        return ctb_sorter(characters, monsters)


@dataclass
class SimulatedEncounter(Encounter):

    def _get_index(self) -> int:
        # simulated encounter don't increment the game's
        # encounter count used to calculate aeons' stats
        return self.gamestate.encounters_count

    def _get_formation(self) -> Formation:
        return SIMULATIONS[self.name].monsters


@dataclass
class RandomEncounter(Encounter):

    def __post_init__(self) -> None:
        self.zone = ZONES[self.name]
        super().__post_init__()
        self.random_index = self._get_random_index()
        self.zone_index = self._get_zone_index()

    def __str__(self) -> str:
        string = super().__str__()
        string = (f'{string[:13]}'
                  f'|{self.random_index:3}|{self.zone_index:3}'
                  f'{string[13:]}')
        return string

    def _get_formation(self) -> Formation:
        rng_value = self._advance_rng(1)
        formation_index = rng_value % len(self.zone.formations)
        return self.zone.formations[formation_index]

    def _get_random_index(self) -> int:
        self.gamestate.random_encounters_count += 1
        return self.gamestate.random_encounters_count

    def _get_zone_index(self) -> int:
        index = self.gamestate.zone_encounters_counts.get(self.name, 0) + 1
        self.gamestate.zone_encounters_counts[self.name] = index
        return index


@dataclass
class MultizoneRandomEncounter(Event):
    zones: list[str]

    def __post_init__(self) -> None:
        self.encounters = self._get_encounters()

    def __str__(self) -> str:
        string = ''
        zones_names = []
        formations = []
        for count, enc in enumerate(self.encounters, 1):
            if count == 1:
                string += str(enc)[:24]
            zone_name = ZONES[enc.name].name
            zones_names.append(zone_name)
            formation = f'[{enc.formation}]'
            formations.append(formation)
        string += (f'{"/".join(zones_names)}: {"/".join(formations)} '
                   f'{enc.condition}')
        return string

    def _get_encounters(self) -> list[RandomEncounter]:
        encounters = []
        tracker = self.gamestate._rng_tracker
        saved_rng_positions = tracker._rng_current_positions.copy()
        for count, zone in enumerate(self.zones, 1):
            encounter = RandomEncounter(
                gamestate=self.gamestate,
                name=zone,
            )
            encounters.append(encounter)
            if count < len(self.zones):
                self.gamestate.encounters_count -= 1
                self.gamestate.random_encounters_count -= 1
                tracker._rng_current_positions.clear()
                tracker._rng_current_positions.extend(saved_rng_positions)
        return encounters
