from dataclasses import dataclass

from .constants import Element, Status


@dataclass(frozen=True)
class StatusApplication:
    status: Status
    chance: int
    stacks: int


NUL_STATUSES = {
    Element.FIRE: Status.NULBLAZE,
    Element.ICE: Status.NULFROST,
    Element.THUNDER: Status.NULSHOCK,
    Element.WATER: Status.NULTIDE,
}
NO_RNG_STATUSES = (
    Status.SCAN,
    Status.POWER_DISTILLER,
    Status.MANA_DISTILLER,
    Status.SPEED_DISTILLER,
    Status.ABILITY_DISTILLER,
    Status.SHIELD,
    Status.BOOST,
    Status.EJECT,
    Status.AUTOLIFE,
    Status.CURSE,
    Status.DEFEND,
    Status.GUARD,
    Status.SENTINEL,
    Status.DOOM,
    Status.MAX_HP_X_2,
    Status.MAX_MP_X_2,
    Status.MP_0,
    Status.DAMAGE_9999,
    Status.CRITICAL,
    Status.OVERDRIVE_X_1_5,
    Status.OVERDRIVE_X_2,
    )
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
