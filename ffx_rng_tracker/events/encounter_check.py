from dataclasses import dataclass, field
from typing import Iterator

from ..data.encounter_formations import Zone
from .main import Event, GameState


@dataclass
class EncounterCheck(Event):
    max_steps: int
    zone: Zone
    encounter: bool = field(init=False, repr=False)
    steps: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.encounter, self.steps = self.check_encounter()

    def __str__(self) -> str:
        string = f'{self.zone.name}'
        if self.encounter:
            string += f'Encounter at step {self.steps}'
        else:
            string += f'No encounters for {self.steps} steps'
        return string

    def check_encounter(self) -> tuple[bool, int]:
        live_steps = max(self.max_steps - self.zone.grace_period, 0)
        if live_steps == 0:
            return False, self.max_steps
        for steps in range(1, live_steps + 1):
            rng_roll = self._advance_rng(0) & 255
            counter = steps * 256 // self.zone.threat_modifier
            if rng_roll < counter:
                encounter = True
                break
        else:
            encounter = False
        return encounter, self.zone.grace_period + steps


def walk(
        gamestate: GameState, steps: int,
        zone: Zone) -> Iterator[EncounterCheck]:
    while steps > 0:
        encounter_check = EncounterCheck(gamestate, steps, zone)
        yield encounter_check
        steps -= encounter_check.steps
