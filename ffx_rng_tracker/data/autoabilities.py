import csv

from ..utils import open_cp1252
from .constants import Autoability, Element, Status
from .file_functions import get_resource_path
from .statuses import StatusApplication


def _get_autoabilities_gil_values(file_path: str) -> dict[Autoability, int]:
    """Retrieves autoabilities gil values."""
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        abilities_file_reader = csv.reader(file_object)
        # skips first line
        next(abilities_file_reader)
        autoabilities = {}
        for line in abilities_file_reader:
            autoabilities[Autoability(line[0])] = int(line[1])
    return autoabilities


GIL_VALUES = _get_autoabilities_gil_values('data_files/autoabilities.csv')
AUTOABILITIES = [a for a in Autoability]
ELEMENTAL_STRIKES = {
    Autoability.FIRESTRIKE: Element.FIRE,
    Autoability.ICESTRIKE: Element.ICE,
    Autoability.LIGHTNINGSTRIKE: Element.THUNDER,
    Autoability.WATERSTRIKE: Element.WATER,
}
ELEMENTAL_WARDS = {
    Autoability.FIRE_WARD: Element.FIRE,
    Autoability.ICE_WARD: Element.ICE,
    Autoability.LIGHTNING_WARD: Element.THUNDER,
    Autoability.WATER_WARD: Element.WATER,
}
ELEMENTAL_PROOFS = {
    Autoability.FIREPROOF: Element.FIRE,
    Autoability.ICEPROOF: Element.ICE,
    Autoability.LIGHTNINGPROOF: Element.THUNDER,
    Autoability.WATERPROOF: Element.WATER,
}
ELEMENTAL_EATERS = {
    Autoability.FIRE_EATER: Element.FIRE,
    Autoability.ICE_EATER: Element.ICE,
    Autoability.LIGHTNING_EATER: Element.THUNDER,
    Autoability.WATER_EATER: Element.WATER,
}
STATUS_TOUCHES = {
    Autoability.DEATHTOUCH: StatusApplication(Status.DEATH, 50, 254),
    Autoability.ZOMBIETOUCH: StatusApplication(Status.ZOMBIE, 50, 254),
    Autoability.STONETOUCH: StatusApplication(Status.PETRIFY, 50, 254),
    Autoability.POISONTOUCH: StatusApplication(Status.POISON, 50, 254),
    Autoability.SLEEPTOUCH: StatusApplication(Status.SLEEP, 50, 254),
    Autoability.SILENCETOUCH: StatusApplication(Status.SILENCE, 50, 254),
    Autoability.DARKTOUCH: StatusApplication(Status.DARK, 50, 254),
    Autoability.SLOWTOUCH: StatusApplication(Status.SLOW, 50, 254),
}
STATUS_STRIKES = {
    Autoability.DEATHSTRIKE: StatusApplication(Status.DEATH, 100, 254),
    Autoability.ZOMBIESTRIKE: StatusApplication(Status.ZOMBIE, 100, 254),
    Autoability.STONESTRIKE: StatusApplication(Status.PETRIFY, 100, 254),
    Autoability.POISONSTRIKE: StatusApplication(Status.POISON, 100, 254),
    Autoability.SLEEPSTRIKE: StatusApplication(Status.SLEEP, 100, 254),
    Autoability.SILENCESTRIKE: StatusApplication(Status.SILENCE, 100, 254),
    Autoability.DARKSTRIKE: StatusApplication(Status.DARK, 100, 254),
    Autoability.SLOWSTRIKE: StatusApplication(Status.SLOW, 100, 254),
}
STATUS_WARDS = {
    Autoability.DEATH_WARD: Status.DEATH,
    Autoability.ZOMBIE_WARD: Status.ZOMBIE,
    Autoability.STONE_WARD: Status.PETRIFY,
    Autoability.POISON_WARD: Status.POISON,
    Autoability.SLEEP_WARD: Status.SLEEP,
    Autoability.SILENCE_WARD: Status.SILENCE,
    Autoability.DARK_WARD: Status.DARK,
    Autoability.SLOW_WARD: Status.SLOW,
    Autoability.CONFUSE_WARD: Status.CONFUSE,
    Autoability.BERSERK_WARD: Status.BERSERK,
    Autoability.CURSE_WARD: Status.CURSE,
}
STATUS_PROOFS = {
    Autoability.DEATHPROOF: Status.DEATH,
    Autoability.ZOMBIEPROOF: Status.ZOMBIE,
    Autoability.STONEPROOF: Status.PETRIFY,
    Autoability.POISONPROOF: Status.POISON,
    Autoability.SLEEPPROOF: Status.SLEEP,
    Autoability.SILENCEPROOF: Status.SILENCE,
    Autoability.DARKPROOF: Status.DARK,
    Autoability.SLOWPROOF: Status.SLOW,
    Autoability.CONFUSEPROOF: Status.CONFUSE,
    Autoability.BERSERKPROOF: Status.BERSERK,
    Autoability.CURSEPROOF: Status.CURSE,
}
STRENGTH_BONUSES = {
    Autoability.STRENGTH_3: 3,
    Autoability.STRENGTH_5: 5,
    Autoability.STRENGTH_10: 10,
    Autoability.STRENGTH_20: 20,
}
MAGIC_BONUSES = {
    Autoability.MAGIC_3: 3,
    Autoability.MAGIC_5: 5,
    Autoability.MAGIC_10: 10,
    Autoability.MAGIC_20: 20,
}
DEFENSE_BONUSES = {
    Autoability.DEFENSE_3: 3,
    Autoability.DEFENSE_5: 5,
    Autoability.DEFENSE_10: 10,
    Autoability.DEFENSE_20: 20,
}
MAGIC_DEF_BONUSES = {
    Autoability.MAGIC_DEF_3: 3,
    Autoability.MAGIC_DEF_5: 5,
    Autoability.MAGIC_DEF_10: 10,
    Autoability.MAGIC_DEF_20: 20,
}
HP_BONUSES = {
    Autoability.HP_5: 5,
    Autoability.HP_10: 10,
    Autoability.HP_20: 20,
    Autoability.HP_30: 30,
}
MP_BONUSES = {
    Autoability.MP_5: 5,
    Autoability.MP_10: 10,
    Autoability.MP_20: 20,
    Autoability.MP_30: 30,
}
AUTO_STATUSES = {
    Autoability.AUTO_SHELL: Status.SHELL,
    Autoability.AUTO_PROTECT: Status.PROTECT,
    Autoability.AUTO_HASTE: Status.HASTE,
    Autoability.AUTO_REGEN: Status.REGEN,
    Autoability.AUTO_REFLECT: Status.REFLECT,
}
ELEMENTAL_SOS_AUTO_STATUSES = {
    Autoability.SOS_NULTIDE: Status.NULTIDE,
    Autoability.SOS_NULFROST: Status.NULFROST,
    Autoability.SOS_NULSHOCK: Status.NULSHOCK,
    Autoability.SOS_NULBLAZE: Status.NULBLAZE,
}
SOS_AUTO_STATUSES = {
    Autoability.SOS_SHELL: Status.SHELL,
    Autoability.SOS_PROTECT: Status.PROTECT,
    Autoability.SOS_HASTE: Status.HASTE,
    Autoability.SOS_REGEN: Status.REGEN,
    Autoability.SOS_REFLECT: Status.REFLECT,
}
RIBBON_IMMUNITIES = (
    Status.ZOMBIE,
    Status.PETRIFY,
    Status.POISON,
    Status.CONFUSE,
    Status.BERSERK,
    Status.PROVOKE,
    Status.SLEEP,
    Status.SILENCE,
    Status.DARK,
    Status.SLOW,
    Status.DOOM,
)
AEON_RIBBON_IMMUNITIES = (
    Status.DEATH,
    Status.ZOMBIE,
    Status.PETRIFY,
    Status.POISON,
    Status.POWER_BREAK,
    Status.MAGIC_BREAK,
    Status.ARMOR_BREAK,
    Status.MENTAL_BREAK,
    Status.CONFUSE,
    Status.BERSERK,
    Status.PROVOKE,
    Status.SLEEP,
    Status.SILENCE,
    Status.DARK,
    Status.SLOW,
    Status.POWER_DISTILLER,
    Status.MANA_DISTILLER,
    Status.SPEED_DISTILLER,
    Status.ABILITY_DISTILLER,
    Status.SCAN,
    Status.DOOM,
)
