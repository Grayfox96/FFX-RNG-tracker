from dataclasses import dataclass, field

from ..data.encounter_formations import Zone
from .main import Event


@dataclass
class EncounterCheck(Event):
    zone: Zone
    max_distance: int
    encounter: bool = field(init=False, repr=False)
    distance: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.encounter, self.distance = self.check_encounter()

    def __str__(self) -> str:
        string = f'{self.zone}: '
        if self.encounter:
            string += f'Encounter at {self.distance} units'
        else:
            string += f'No encounters for {self.distance} units'
        return string

    def check_encounter(self) -> tuple[bool, int]:
        steps = self.max_distance // 10
        live_steps = max(steps - self.zone.grace_period, 0)
        if live_steps == 0:
            return False, self.max_distance
        for steps in range(1, live_steps + 1):
            rng_roll = self._advance_rng(0) & 255
            counter = steps * 256 // self.zone.threat_modifier
            if rng_roll < counter:
                encounter = True
                distance = (self.zone.grace_period + steps) * 10
                break
        else:
            encounter = False
            distance = self.max_distance
        return encounter, distance


@dataclass
class EncounterChecks(Event):
    zone: Zone
    max_distance: int
    checks: list[EncounterCheck] = field(
        default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self.checks = self._perform_checks()

    def __str__(self) -> str:
        string = f'{self.zone}:'
        n_of_encs = sum([1 for c in self.checks if c.encounter])
        total_distance = 0
        encounters = []
        for check in self.checks:
            if check.encounter:
                total_distance += check.distance
                encounters.append(f'{total_distance // 10}')
        if n_of_encs:
            string += (f' {n_of_encs} encounters'
                       f' at steps {", ".join(encounters)}')
        else:
            string += ' no encounters'
        if len(self.checks) == n_of_encs:
            string += ' (0 steps before end of the zone)'
        else:
            string += f' ({check.distance // 10} steps before end of the zone)'

        return string

    def _perform_checks(self) -> list[EncounterCheck]:
        distance = self.max_distance
        checks = []
        while distance > 0:
            check = EncounterCheck(self.gamestate, self.zone, distance)
            checks.append(check)
            distance -= check.distance
        return checks
