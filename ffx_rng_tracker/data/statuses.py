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
NO_RNG_STATUSES = {
    Status.DEFEND,
    Status.SHIELD,
    Status.BOOST,
    Status.DELAY_WEAK,
    Status.DELAY_STRONG,
    Status.POWER_DISTILLER,
    Status.MANA_DISTILLER,
    Status.SPEED_DISTILLER,
    Status.ABILITY_DISTILLER,
    Status.GUARD,
    Status.SENTINEL,
    Status.SCAN,
    Status.LIFE,
    Status.AUTOLIFE,
    Status.EJECT,
    Status.DOOM,
    Status.CURSE,
    Status.MAX_HP_X_2,
    Status.MAX_MP_X_2,
    Status.MP_0,
    Status.CRITICAL,
    Status.DAMAGE_9999,
    Status.OVERDRIVE_X1_5,
    Status.OVERDRIVE_X_2,
    Status.ESCAPE,
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
