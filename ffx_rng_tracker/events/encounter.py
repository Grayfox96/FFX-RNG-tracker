from dataclasses import dataclass, field

from ..data.constants import ICV_BASE, ICV_VARIANCE, EncounterCondition, Stat
from ..data.encounter_formations import FORMATIONS, Formation
from .main import Event


@dataclass
class Encounter(Event):
    name: str
    initiative: bool
    forced_condition: EncounterCondition | None = None
    formation: Formation = field(init=False, repr=False)
    condition: EncounterCondition = field(init=False, repr=False)
    index: int = field(init=False, repr=False)
    icvs: dict[str, int] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.formation = self._get_formation()
        self.condition = self._get_condition()
        self.index = self._get_index()
        self.icvs = self._get_icvs()

    def __str__(self) -> str:
        if self.condition == EncounterCondition.NORMAL:
            condition = ''
        else:
            condition = f' {self.condition}'
        name = FORMATIONS.bosses[self.name].name
        formation = ', '.join([str(m) for m in self.formation])
        string = (f'Encounter {self.index:3}: {name} '
                  f'[{formation}]{condition}')
        return string

    def _get_index(self) -> int:
        self.gamestate.encounters_count += 1
        return self.gamestate.encounters_count

    def _get_formation(self) -> Formation:
        return FORMATIONS.bosses[self.name].formation

    def _get_condition(self) -> EncounterCondition:
        condition_rng = self._advance_rng(1) & 255
        if self.forced_condition:
            return self.forced_condition
        if self.initiative:
            condition_rng -= 33
        if condition_rng < 32:
            return EncounterCondition.PREEMPTIVE
        elif condition_rng < 255 - 32:
            return EncounterCondition.NORMAL
        else:
            return EncounterCondition.AMBUSH

    def _get_icvs(self) -> dict[str, int]:
        icvs = {}
        if self.condition is EncounterCondition.PREEMPTIVE:
            for c in self.gamestate.characters.values():
                icvs[c.name] = 0
        elif self.condition is EncounterCondition.AMBUSH:
            for c in self.gamestate.characters.values():
                icvs[c.name] = ICV_BASE[c.stats[Stat.AGILITY]] * 3
        else:
            for c in self.gamestate.characters.values():
                base = ICV_BASE[c.stats[Stat.AGILITY]] * 3
                index = c.index + 20 if c.index < 7 else 27
                variance_rng = self._advance_rng(index)
                variance = ICV_VARIANCE[c.stats[Stat.AGILITY]] + 1
                variance = variance_rng % variance
                icvs[c.name] = base - variance
        return icvs

    def rollback(self) -> None:
        self.gamestate.encounters_count -= 1
        return super().rollback()


@dataclass
class SimulatedEncounter(Encounter):

    def __str__(self) -> str:
        if self.condition == EncounterCondition.NORMAL:
            condition = ''
        else:
            condition = f' {self.condition}'
        name = FORMATIONS.simulated[self.name][0]
        formation = ' or '.join([str(m) for m in self.formation])
        string = (f'Encounter {self.index:3}: {name} '
                  f'({formation}){condition}')
        return string

    def _get_index(self) -> int:
        # simulated encounter don't increment the game's
        # encounter count used to calculate aeons' stats
        return self.gamestate.encounters_count

    def _get_formation(self) -> Formation:
        return FORMATIONS.simulated[self.name][1]

    def rollback(self) -> None:
        self.gamestate.encounters_count += 1
        return super().rollback()


@dataclass
class RandomEncounter(Encounter):
    zone: str = field(init=False, repr=False)
    random_index: int = field(init=False, repr=False)
    zone_index: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.zone = self.name
        super().__post_init__()
        self.random_index = self._get_random_index()
        self.zone_index = self._get_zone_index()
        self.name = self._get_name()

    def __str__(self) -> str:
        if self.condition == EncounterCondition.NORMAL:
            condition = ''
        else:
            condition = f' {self.condition}'
        zone = FORMATIONS.zones[self.zone].name
        formation = ', '.join([str(m) for m in self.formation])
        string = (f'Encounter {self.index:3}|{self.random_index:3}|'
                  f'{self.zone_index:3}: {zone}: {formation}{condition}')
        return string

    def _get_formation(self) -> Formation:
        rng_value = self._advance_rng(1)
        zone = FORMATIONS.zones[self.zone]
        formation_index = rng_value % len(zone.formations)
        return zone.formations[formation_index]

    def _get_random_index(self) -> int:
        self.gamestate.random_encounters_count += 1
        return self.gamestate.random_encounters_count

    def _get_zone_index(self) -> int:
        index = self.gamestate.zone_encounters_counts.get(self.zone, 0) + 1
        self.gamestate.zone_encounters_counts[self.zone] = index
        return index

    def _get_name(self) -> str:
        return f'{self.zone} [{self.zone_index}]'

    def rollback(self) -> None:
        self.gamestate.random_encounters_count -= 1
        self.gamestate.zone_encounters_counts[self.zone] -= 1
        return super().rollback()


@dataclass
class MultizoneRandomEncounter(Event):
    zones: list[str]
    initiative: bool
    forced_condition: EncounterCondition | None = None
    encounters: list[RandomEncounter] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.encounters = self._get_encounters()

    def __str__(self) -> str:
        string = ''
        zones = []
        formations = []
        for count, enc in enumerate(self.encounters):
            if count == 0:
                if enc.condition == EncounterCondition.NORMAL:
                    condition = ''
                else:
                    condition = f' {enc.condition}'
                string += (f'Encounter {enc.index:3}|'
                           f'{enc.random_index:3}|'
                           f'{enc.zone_index:3}| ')
            zones.append(FORMATIONS.zones[enc.zone].name)
            formations.append(
                f'[{", ".join([str(m) for m in enc.formation])}]')
        string += f'{"/".join(zones)}: {"/".join(formations)}{condition}'
        return string

    def _get_encounters(self) -> list[RandomEncounter]:
        encounters = []
        for count, zone in enumerate(self.zones, 1):
            encounter = RandomEncounter(
                gamestate=self.gamestate,
                name=zone,
                initiative=self.initiative,
                forced_condition=self.forced_condition,
            )
            encounters.append(encounter)
            if count < len(self.zones):
                encounter.rollback()
                self.gamestate.zone_encounters_counts[zone] += 1
        return encounters
