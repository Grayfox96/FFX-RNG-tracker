from dataclasses import dataclass

from .constants import Element, Status


@dataclass(frozen=True)
class StatusApplication:
    status: Status
    chance: int
    stacks: int

    def __str__(self) -> str:
        return f'{self.chance}/101 x{self.stacks}'


NUL_STATUSES = {
    Element.FIRE: Status.NULBLAZE,
    Element.ICE: Status.NULFROST,
    Element.THUNDER: Status.NULSHOCK,
    Element.WATER: Status.NULTIDE,
}
TEMPORARY_STATUSES = {
    Status.DEFEND,
    Status.SHIELD,
    Status.BOOST,
    Status.GUARD,
    Status.SENTINEL,
}
DURATION_STATUSES = {
    Status.SLEEP,
    Status.SILENCE,
    Status.DARK,
    Status.REGEN,
    Status.SLOW,
}
