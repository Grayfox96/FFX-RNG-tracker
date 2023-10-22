from dataclasses import dataclass

from ..data.encounter_formations import Zone
from .main import Event


@dataclass
class EncounterCheck(Event):
    zone: Zone
    max_distance: int

    def __post_init__(self) -> None:
        self.encounter, self.distance = self.check_encounter()
        if self.encounter:
            self.gamestate.live_distance = 0
        else:
            self.gamestate.live_distance = self.distance

    def __str__(self) -> str:
        string = f'{self.zone}: '
        if self.encounter:
            string += f'Encounter at {self.distance} units'
        else:
            string += f'No encounters for {self.distance} units'
        return string

    def check_encounter(self) -> tuple[bool, int]:
        max_steps = (self.gamestate.live_distance + self.max_distance) // 10
        starting_steps = self.gamestate.live_distance // 10
        max_steps -= self.zone.grace_period
        starting_steps = max(0, starting_steps - self.zone.grace_period)
        if max_steps <= 0:
            return False, self.max_distance
        for steps in range(starting_steps + 1, max_steps + 1):
            rng_roll = self._advance_rng(0) & 255
            counter = steps * 256 // self.zone.threat_modifier
            if rng_roll < counter:
                distance = (self.zone.grace_period + steps) * 10 - self.gamestate.live_distance
                return True, distance
        return False, self.max_distance


@dataclass
class EncounterChecks(Event):
    zone: Zone
    max_distance: int
    continue_previous_zone: bool

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
                       f' at steps {', '.join(encounters)}')
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
        if not self.continue_previous_zone:
            self.gamestate.live_distance = 0
        while distance > 0:
            check = EncounterCheck(self.gamestate, self.zone, distance)
            checks.append(check)
            distance -= check.distance
        return checks
