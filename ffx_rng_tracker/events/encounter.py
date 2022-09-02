from dataclasses import dataclass, field

from ..data.constants import (ICV_BASE, ICV_VARIANCE, Autoability, Character,
                              EncounterCondition, Stat)
from ..data.encounter_formations import (BOSSES, FORMATIONS, SIMULATIONS,
                                         ZONES, Formation, Zone)
from .main import Event


@dataclass
class Encounter(Event):
    name: str
    formation: Formation = field(init=False, repr=False)
    condition: EncounterCondition = field(init=False, repr=False)
    index: int = field(init=False, repr=False)
    party_icvs: dict[Character, int] = field(init=False, repr=False)
    monsters_icvs: list[int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.formation = self._get_formation()
        self.condition = self._get_condition()
        self.index = self._get_index()
        self._duplicate_monsters_rng_advances()
        self.party_icvs = self._get_party_icvs()
        self.monsters_icvs = self._get_enemies_icvs()

    def __str__(self) -> str:
        icvs: list[tuple[str, str]] = []

        for character, icv in self.party_icvs.items():
            c = self.gamestate.characters[character]
            sort_key = f'{icv:03}0{256 - c.stats[Stat.AGILITY]:03}{c.index:02}'
            string = f'{character[:2]:2}[{icv:2}]'
            icvs.append((sort_key, string))

        for index, icv in enumerate(self.monsters_icvs):
            stats = self.formation[index].stats
            sort_key = f'{icv:03}1{256 - stats[Stat.AGILITY]:03}{index + 8:02}'
            string = f'M{index + 1}[{icv:2}]'
            icvs.append((sort_key, string))

        # sorting by icv, then by party, then by agility and finally by index
        icvs.sort(key=lambda v: v[0])
        icvs = [v[1] for v in icvs]

        name = FORMATIONS[self.name].name
        string = (f'Encounter {self.index:3} - {name}: {self.formation} '
                  f'{self.condition} {" ".join(icvs)}')
        return string

    def _get_index(self) -> int:
        self.gamestate.encounters_count += 1
        return self.gamestate.encounters_count

    def _get_formation(self) -> Formation:
        return BOSSES[self.name].formation

    def _get_condition(self) -> EncounterCondition:
        for character in self.gamestate.party:
            character_data = self.gamestate.characters[character]
            if Autoability.INITIATIVE in character_data.autoabilities:
                initiative = True
                break
        else:
            initiative = False
        condition_rng = self._advance_rng(1) & 255
        if FORMATIONS[self.name].forced_condition is not None:
            return FORMATIONS[self.name].forced_condition
        if initiative:
            condition_rng -= 33
        if condition_rng < 32:
            return EncounterCondition.PREEMPTIVE
        elif condition_rng < 255 - 32:
            return EncounterCondition.NORMAL
        else:
            return EncounterCondition.AMBUSH

    def _duplicate_monsters_rng_advances(self) -> None:
        for index, monster in enumerate(self.formation):
            count = self.formation.count(monster)
            if count > 1:
                if self.formation.index(monster) == index:
                    for _ in range(count):
                        self._advance_rng(28 + index)
                self._advance_rng(28 + index)

    def _get_party_icvs(self) -> dict[str, int]:
        icvs = {}
        if self.condition is EncounterCondition.PREEMPTIVE:
            for character in self.gamestate.party:
                icvs[character] = 0
        elif self.condition is EncounterCondition.AMBUSH:
            for character, state in self.gamestate.characters.items():
                if character not in self.gamestate.party:
                    continue
                icvs[character] = ICV_BASE[state.stats[Stat.AGILITY]] * 3
        else:
            for character, state in self.gamestate.characters.items():
                index = min(20 + state.index, 27)
                if character not in self.gamestate.party:
                    self._advance_rng(index)
                    continue
                variance_rng = self._advance_rng(index)
                variance = ICV_VARIANCE[state.stats[Stat.AGILITY]] + 1
                variance = variance_rng % variance
                base = ICV_BASE[state.stats[Stat.AGILITY]] * 3
                icvs[character] = base - variance
        for character in icvs:
            state = self.gamestate.characters[character]
            if Autoability.FIRST_STRIKE in state.autoabilities:
                icvs[character] = 0
            elif (Autoability.AUTO_HASTE in state.autoabilities
                    or (Autoability.SOS_HASTE in state.autoabilities
                        and state.in_crit)):
                icvs[character] = icvs[character] // 2
        return icvs

    def _get_enemies_icvs(self) -> list[int]:
        icvs = []
        if self.condition is EncounterCondition.PREEMPTIVE:
            for m in self.formation:
                icvs.append(ICV_BASE[m.stats[Stat.AGILITY]] * 3)
        elif self.condition is EncounterCondition.AMBUSH:
            for m in self.formation:
                icvs.append(0)
        else:
            for index, m in enumerate(self.formation):
                base = ICV_BASE[m.stats[Stat.AGILITY]] * 3 * 100
                index = index + 28 if index < 7 else 35
                variance_rng = self._advance_rng(index)
                variance = 100 - (variance_rng % 11)
                icvs.append(base // variance)
            # empty enemy party slots still advance rng
            for index in range(28 + len(self.formation), 36):
                self._advance_rng(index)
        return icvs

    def rollback(self) -> None:
        self.gamestate.encounters_count -= 1
        return super().rollback()


@dataclass
class SimulatedEncounter(Encounter):

    def _get_index(self) -> int:
        # simulated encounter don't increment the game's
        # encounter count used to calculate aeons' stats
        return self.gamestate.encounters_count

    def _get_formation(self) -> Formation:
        return SIMULATIONS[self.name].monsters

    def rollback(self) -> None:
        self.gamestate.encounters_count += 1
        return super().rollback()


@dataclass
class RandomEncounter(Encounter):
    zone: Zone = field(init=False, repr=False)
    random_index: int = field(init=False, repr=False)
    zone_index: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
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
        zone = ZONES[self.name]
        formation_index = rng_value % len(zone.formations)
        return zone.formations[formation_index]

    def _get_random_index(self) -> int:
        self.gamestate.random_encounters_count += 1
        return self.gamestate.random_encounters_count

    def _get_zone_index(self) -> int:
        index = self.gamestate.zone_encounters_counts.get(self.name, 0) + 1
        self.gamestate.zone_encounters_counts[self.name] = index
        return index

    def rollback(self) -> None:
        self.gamestate.random_encounters_count -= 1
        self.gamestate.zone_encounters_counts[self.name] -= 1
        return super().rollback()


@dataclass
class MultizoneRandomEncounter(Event):
    zones: list[str]
    encounters: list[RandomEncounter] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.encounters = self._get_encounters()

    def __str__(self) -> str:
        string = ''
        zones = []
        formations = []
        for count, enc in enumerate(self.encounters, 1):
            if count == 1:
                string += str(enc)[:24]
            zone = ZONES[enc.name].name
            zones.append(zone)
            formation = f'[{enc.formation}]'
            formations.append(formation)
            if count == len(self.encounters):
                string += (f'{"/".join(zones)}: {"/".join(formations)} '
                           f'{enc.condition}')
        return string

    def _get_encounters(self) -> list[RandomEncounter]:
        encounters = []
        for count, zone in enumerate(self.zones, 1):
            encounter = RandomEncounter(
                gamestate=self.gamestate,
                name=zone,
            )
            encounters.append(encounter)
            if count < len(self.zones):
                encounter.rollback()
                self.gamestate.zone_encounters_counts[zone] += 1
        return encounters

    def rollback(self) -> None:
        if self.encounters:
            self.encounters[-1].rollback()
        return super().rollback()
