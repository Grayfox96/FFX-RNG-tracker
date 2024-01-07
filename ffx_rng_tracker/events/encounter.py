from dataclasses import dataclass

from ..data.actor import MonsterActor
from ..data.constants import (ICV_VARIANCE, Autoability, Character,
                              EncounterCondition, MonsterSlot, Stat, Status)
from ..data.encounter_formations import (BOSSES, FORMATIONS, SIMULATIONS,
                                         ZONES, Formation)
from ..ui_functions import ctb_sorter
from .main import Event


@dataclass
class Encounter(Event):
    name: str

    def __post_init__(self) -> None:
        self.gamestate.process_start_of_encounter()
        self.formation = self._get_formation()
        self._update_party()
        self._update_current_monster_formation()
        self.condition = self._get_condition()
        self.index = self._get_index()
        self._duplicate_monsters_rng_advances()
        self._set_party_icvs()
        self._set_monsters_icvs()
        self.icvs_string = self._get_icvs_string()
        self.gamestate.normalize_ctbs(self.gamestate.get_min_ctb())

    def __str__(self) -> str:
        string = (f'Encounter: {self.index:>3} | '
                  f'{FORMATIONS[self.name].name} | '
                  f'{self.formation} {self.condition} | '
                  f'{self.icvs_string}')
        return string

    def _get_index(self) -> int:
        self.gamestate.encounters_count += 1
        return self.gamestate.encounters_count

    def _get_formation(self) -> Formation:
        return BOSSES[self.name].formation

    def _update_party(self) -> None:
        if self.name not in BOSSES:
            return
        boss = BOSSES[self.name]
        if boss.forced_party:
            self.gamestate.party = boss.forced_party

    def _update_current_monster_formation(self) -> None:
        for monster, slot in zip(self.formation.monsters, MonsterSlot):
            self.gamestate.monster_party.append(MonsterActor(monster, slot))

    def _get_condition(self) -> EncounterCondition:
        condition_rng = self._advance_rng(1) & 255
        if self.formation.forced_condition is not None:
            return self.formation.forced_condition
        for character in self.gamestate.party:
            actor = self.gamestate.characters[character]
            if Autoability.INITIATIVE in actor.autoabilities:
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

    def _set_party_icvs(self) -> None:
        if self.condition is EncounterCondition.PREEMPTIVE:
            return
        elif self.condition is EncounterCondition.AMBUSH:
            for character in self.gamestate.party:
                actor = self.gamestate.characters[character]
                if actor.first_strike:
                    continue
                icv = actor.base_ctb * 3
                if Status.HASTE in actor.statuses:
                    icv = icv // 2
                actor.ctb = icv
        else:
            for character, actor in self.gamestate.characters.items():
                if character is Character.UNKNOWN:
                    continue
                index = min(20 + actor.index, 27)
                variance_rng = self._advance_rng(index)
                if character not in self.gamestate.party or actor.first_strike:
                    continue
                variance = ICV_VARIANCE[actor.stats[Stat.AGILITY]] + 1
                icv = actor.base_ctb * 3 - (variance_rng % variance)
                if Status.HASTE in actor.statuses:
                    icv = icv // 2
                actor.ctb = icv

    def _set_monsters_icvs(self) -> None:
        if self.condition is EncounterCondition.PREEMPTIVE:
            for actor in self.gamestate.monster_party:
                actor.ctb = actor.base_ctb * 3
        elif self.condition is EncounterCondition.AMBUSH:
            return
        else:
            for actor in self.gamestate.monster_party:
                index = min(actor.index + 28, 35)
                variance_rng = self._advance_rng(index)
                variance = 100 - (variance_rng % 11)
                actor.ctb = (actor.base_ctb * 3 * 100) // variance
            # empty monster party slots still advance rng
            for index in range(28 + len(self.formation.monsters), 36):
                self._advance_rng(index)

    def _get_icvs_string(self) -> str:
        characters = [actor for c, actor in self.gamestate.characters.items()
                      if c in self.gamestate.party]
        return ctb_sorter(characters, self.gamestate.monster_party)


@dataclass
class SimulatedEncounter(Encounter):

    def __str__(self) -> str:
        return 'Simulated ' + super().__str__()

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
        string = 'Random ' + super().__str__()
        parts = string.split('|')
        parts[0] += f'{self.random_index:>3} {self.zone_index:>3} '
        return '|'.join(parts)

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
                string += str(enc).split('|')[0]
            zone_name = ZONES[enc.name].name
            zones_names.append(zone_name)
            formation = f'{enc.formation} {enc.condition}'
            formations.append(formation)
        string += (f' | {'/'.join(zones_names)} | '
                   f'{' | '.join(formations)} | '
                   f'{enc.icvs_string}')
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
