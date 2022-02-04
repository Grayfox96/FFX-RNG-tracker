from dataclasses import dataclass, field

from ..data.characters import CHARACTERS, Character
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
    icvs: dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)

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
        formation = '+'.join([str(m) for m in self.formation])
        string = (f'Encounter {self.index:3}: {self.name} '
                  f'({formation}){condition}')
        return string

    def _get_index(self) -> int:
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, Encounter):
                return event.index + 1
        return 1

    def _get_formation(self) -> Formation:
        return FORMATIONS.set_formation[self.name]

    def _get_condition(self) -> EncounterCondition:
        condition_rng = self._rng_tracker.advance_rng(1) & 255
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

    def _get_icvs(self) -> dict[Character, int]:
        icvs = {}
        if self.condition is EncounterCondition.PREEMPTIVE:
            for c in CHARACTERS.values():
                icvs[c.name] = 0
        elif self.condition is EncounterCondition.AMBUSH:
            for c in CHARACTERS.values():
                icvs[c.name] = ICV_BASE[c.stats[Stat.AGILITY]] * 3
        else:
            for c in CHARACTERS.values():
                base = ICV_BASE[c.stats[Stat.AGILITY]] * 3
                index = c.index + 20 if c.index < 7 else 27
                variance_rng = self._rng_tracker.advance_rng(index)
                variance = ICV_VARIANCE[c.stats[Stat.AGILITY]] + 1
                variance = variance_rng % variance
                icvs[c.name] = base - variance
        return icvs


@dataclass
class SimulatedEncounter(Encounter):

    def _get_index(self) -> int:
        # simulated encounter don't increment the game's
        # encounter count used to calculate aeons' stats
        return super()._get_index() - 1

    def _get_formation(self) -> Formation:
        return FORMATIONS.simulated[self.name]


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

    def __str__(self) -> str:
        if self.condition == EncounterCondition.NORMAL:
            condition = ''
        else:
            condition = f' {self.condition}'
        formation = ', '.join([str(m) for m in self.formation])
        string = (f'Encounter {self.index:3}|{self.random_index:3}|'
                  f'{self.zone_index:3}| {self.zone}: {formation}{condition}')
        return string

    def _get_formation(self) -> Formation:
        rng_value = self._rng_tracker.advance_rng(1)
        zone_formations = FORMATIONS.random[self.zone]
        formation_index = rng_value % len(zone_formations)
        return zone_formations[formation_index]

    def _get_random_index(self) -> int:
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, RandomEncounter):
                return event.random_index + 1
        return 1

    def _get_zone_index(self) -> int:
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, RandomEncounter):
                if event.zone == self.zone:
                    return event.zone_index + 1
        return 1

    def _get_name(self) -> str:
        return f'{self.zone} [{self.zone_index}]'


@dataclass
class MultizoneRandomEncounter(RandomEncounter):

    def __str__(self) -> str:
        if self.condition == EncounterCondition.NORMAL:
            condition = ''
        else:
            condition = f' {self.condition}'
        formations = []
        for f in self.formation:
            formations.append(f'[{", ".join([str(m) for m in f])}]')
        formations = '/'.join(formations)
        string = (f'Encounter {self.index:3}|{self.random_index:3}|'
                  f'{self.zone_index:3}| {self.zone}: {formations}{condition}')
        return string

    def _get_formation(self) -> list[Formation]:
        rng_value = self._rng_tracker.advance_rng(1)
        formations = []
        for zone in self.zone.split('/'):
            zone_formations = FORMATIONS.random[zone]
            formation_index = rng_value % len(zone_formations)
            formations.append(zone_formations[formation_index])
        return formations
