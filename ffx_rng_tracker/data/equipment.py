import json
from dataclasses import dataclass

from ..utils import open_cp1252
from .autoabilities import (AUTO_STATUSES, DEFENSE_BONUSES, ELEMENTAL_EATERS,
                            ELEMENTAL_PROOFS, ELEMENTAL_SOS_AUTO_STATUSES,
                            ELEMENTAL_STRIKES, GIL_VALUES, HP_BONUSES,
                            MAGIC_BONUSES, MAGIC_DEF_BONUSES, MP_BONUSES,
                            SOS_AUTO_STATUSES, STATUS_PROOFS, STATUS_STRIKES,
                            STATUS_TOUCHES, STRENGTH_BONUSES, Autoability)
from .constants import (EQUIPMENT_EMPTY_SLOTS_GIL_MODIFIERS,
                        EQUIPMENT_SLOTS_GIL_MODIFIERS, Character,
                        EquipmentType)
from .file_functions import get_resource_path
from .monsters import Monster


@dataclass
class Equipment:
    owner: Character
    type_: EquipmentType
    slots: int
    abilities: list[Autoability]
    base_weapon_damage: int
    bonus_crit: int

    def __str__(self) -> str:
        abilities = [str(a) for a in self.abilities]
        for _ in range(self.slots - len(abilities)):
            abilities.append('-')
        string = (f'{self.name} '
                  f'({self.owner}) '
                  f'[{", ".join(abilities)}]'
                  f'[{self.gil_value // 4} gil]')
        return string

    @property
    def gil_value(self) -> int:
        empty_slots = self.slots - len(self.abilities)
        abilities_values = [GIL_VALUES[a] for a in self.abilities]
        base_gil_value = sum(abilities_values)
        gil_value = int((50 + base_gil_value)
                        * EQUIPMENT_SLOTS_GIL_MODIFIERS[self.slots]
                        * EQUIPMENT_EMPTY_SLOTS_GIL_MODIFIERS[empty_slots])
        return gil_value

    @property
    def name(self) -> str:
        if self.type_ is EquipmentType.WEAPON:
            name = get_weapon_name(self.owner, self.abilities, self.slots)
        elif self.type_ is EquipmentType.ARMOR:
            name = get_armor_name(self.owner, self.abilities, self.slots)
        return name


@dataclass
class EquipmentDrop:
    equipment: Equipment
    killer: Character
    monster: Monster
    killer_is_owner: bool

    def __str__(self) -> str:
        string = str(self.equipment)
        if self.monster.equipment.drop_chance == 255:
            string += ' (guaranteed)'
        if self.killer_is_owner:
            string += ' (for killer)'
        return string


def _get_equipment_names(file_path: str,
                         ) -> dict[EquipmentType, list[dict[Character, str]]]:
    """Retrieves the equipment names."""
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data: dict[str, list[dict[str, str]]] = json.load(file_object)
    equipment_names: dict[EquipmentType, list] = {}
    for equipment_type, names_dicts in data.items():
        equipment_names[EquipmentType(equipment_type)] = []
        for names_dict in names_dicts:
            names = {}
            for character_name, name in names_dict.items():
                if character_name == 'Description':
                    continue
                character = Character(character_name)
                names[character] = name
            equipment_names[EquipmentType(equipment_type)].append(names)
    return equipment_names


def get_weapon_name(owner: Character,
                    abilities: list[Autoability],
                    slots: int,
                    ) -> str:
    """Returns a weapon's name given the owner,
    the abilities and the number of slots.
    """
    if owner is Character.SEYMOUR:
        return 'Seymour Staff'
    elif owner in tuple(Character)[8:]:
        return f'{owner}\'s weapon'
    # get number of certain ability types in the equipment
    elemental_strikes = 0
    status_strikes = 0
    status_touches = 0
    strength_bonuses = 0
    magic_bonuses = 0
    for ability in abilities:
        if ability in ELEMENTAL_STRIKES:
            elemental_strikes += 1
        elif ability in STATUS_STRIKES:
            status_strikes += 1
        elif ability in STATUS_TOUCHES:
            status_touches += 1
        elif ability in STRENGTH_BONUSES:
            strength_bonuses += 1
        elif ability in MAGIC_BONUSES:
            magic_bonuses += 1
    counter = (Autoability.COUNTERATTACK in abilities
               or Autoability.EVADE_AND_COUNTER in abilities)

    # check conditions for names in order of priority
    if Autoability.CAPTURE in abilities:
        index = 2
    elif elemental_strikes == 4:
        index = 3
    elif Autoability.BREAK_DAMAGE_LIMIT in abilities:
        index = 4
    elif (Autoability.TRIPLE_OVERDRIVE in abilities
            and Autoability.TRIPLE_AP in abilities
            and Autoability.OVERDRIVE_TO_AP in abilities):
        index = 5
    elif (Autoability.TRIPLE_OVERDRIVE in abilities
            and Autoability.OVERDRIVE_TO_AP in abilities):
        index = 6
    elif (Autoability.DOUBLE_OVERDRIVE in abilities
            and Autoability.DOUBLE_AP in abilities):
        index = 7
    elif Autoability.TRIPLE_OVERDRIVE in abilities:
        index = 8
    elif Autoability.DOUBLE_OVERDRIVE in abilities:
        index = 9
    elif Autoability.TRIPLE_AP in abilities:
        index = 10
    elif Autoability.DOUBLE_AP in abilities:
        index = 11
    elif Autoability.OVERDRIVE_TO_AP in abilities:
        index = 12
    elif Autoability.SOS_OVERDRIVE in abilities:
        index = 13
    elif Autoability.ONE_MP_COST in abilities:
        index = 14
    elif status_strikes == 4:
        index = 15
    elif strength_bonuses == 4:
        index = 16
    elif magic_bonuses == 4:
        index = 17
    elif Autoability.MAGIC_BOOSTER in abilities and magic_bonuses == 3:
        index = 18
    elif Autoability.HALF_MP_COST in abilities:
        index = 19
    elif Autoability.GILLIONAIRE in abilities:
        index = 20
    elif elemental_strikes == 3:
        index = 21
    elif status_strikes == 3:
        index = 22
    elif Autoability.MAGIC_COUNTER in abilities and counter:
        index = 23
    elif counter:
        index = 24
    elif Autoability.MAGIC_COUNTER in abilities:
        index = 25
    elif Autoability.MAGIC_BOOSTER in abilities:
        index = 26
    elif Autoability.ALCHEMY in abilities:
        index = 27
    elif Autoability.FIRST_STRIKE in abilities:
        index = 28
    elif Autoability.INITIATIVE in abilities:
        index = 29
    elif Autoability.DEATHSTRIKE in abilities:
        index = 30
    elif Autoability.SLOWSTRIKE in abilities:
        index = 31
    elif Autoability.STONESTRIKE in abilities:
        index = 32
    elif Autoability.POISONSTRIKE in abilities:
        index = 33
    elif Autoability.SLEEPSTRIKE in abilities:
        index = 34
    elif Autoability.SILENCESTRIKE in abilities:
        index = 35
    elif Autoability.DARKSTRIKE in abilities:
        index = 36
    elif strength_bonuses == 3:
        index = 37
    elif magic_bonuses == 3:
        index = 38
    elif elemental_strikes == 2:
        index = 39
    elif status_touches >= 2:
        index = 40
    elif Autoability.DEATHTOUCH in abilities:
        index = 41
    elif Autoability.SLOWTOUCH in abilities:
        index = 42
    elif Autoability.STONETOUCH in abilities:
        index = 43
    elif Autoability.POISONTOUCH in abilities:
        index = 44
    elif Autoability.SLEEPTOUCH in abilities:
        index = 45
    elif Autoability.SILENCETOUCH in abilities:
        index = 46
    elif Autoability.DARKTOUCH in abilities:
        index = 47
    elif Autoability.SENSOR in abilities:
        index = 48
    elif Autoability.FIRESTRIKE in abilities:
        index = 49
    elif Autoability.ICESTRIKE in abilities:
        index = 50
    elif Autoability.LIGHTNINGSTRIKE in abilities:
        index = 51
    elif Autoability.WATERSTRIKE in abilities:
        index = 52
    elif Autoability.DISTILL_POWER in abilities:
        index = 53
    elif Autoability.DISTILL_MANA in abilities:
        index = 54
    elif Autoability.DISTILL_SPEED in abilities:
        index = 55
    elif Autoability.DISTILL_ABILITY in abilities:
        index = 56
    elif slots == 4:
        index = 57
    elif strength_bonuses >= 1 and magic_bonuses >= 1:
        index = 58
    elif slots == 2 or slots == 3:
        index = 59
    elif (Autoability.MAGIC_10 in abilities
            or Autoability.MAGIC_20 in abilities):
        index = 60
    elif (Autoability.STRENGTH_10 in abilities
            or Autoability.STRENGTH_20 in abilities):
        index = 61
    elif Autoability.MAGIC_5 in abilities:
        index = 62
    elif Autoability.MAGIC_3 in abilities:
        index = 63
    elif Autoability.STRENGTH_5 in abilities:
        index = 64
    elif Autoability.STRENGTH_3 in abilities:
        index = 65
    elif Autoability.PIERCING in abilities:
        index = 66
    elif slots == 1:
        index = 67
    else:
        index = 67

    return EQUIPMENT_NAMES[EquipmentType.WEAPON][index][owner]


def get_armor_name(owner: Character,
                   abilities: list[int],
                   slots: int,
                   ) -> str:
    """Returns an armor's name given the owner,
    the abilities and the number of slots.
    """
    if owner is Character.SEYMOUR:
        return 'Seymour Armor'
    elif owner in tuple(Character)[8:]:
        return f'{owner}\'s armor'
    # get number of certain ability types in the equipment
    elemental_eaters = 0
    elemental_proofs = 0
    status_proofs = 0
    defense_bonuses = 0
    magic_def_bonuses = 0
    hp_bonuses = 0
    mp_bonuses = 0
    auto_statuses = 0
    elemental_sos_auto_statuses = 0
    status_soses = 0
    for ability in abilities:
        if ability in ELEMENTAL_EATERS:
            elemental_eaters += 1
        elif ability in ELEMENTAL_PROOFS:
            elemental_proofs += 1
        elif ability in STATUS_PROOFS:
            status_proofs += 1
        elif ability in DEFENSE_BONUSES:
            defense_bonuses += 1
        elif ability in MAGIC_DEF_BONUSES:
            magic_def_bonuses += 1
        elif ability in HP_BONUSES:
            hp_bonuses += 1
        elif ability in MP_BONUSES:
            mp_bonuses += 1
        elif ability in AUTO_STATUSES:
            auto_statuses += 1
        elif ability in ELEMENTAL_SOS_AUTO_STATUSES:
            elemental_sos_auto_statuses += 1
        elif ability in SOS_AUTO_STATUSES:
            status_soses += 1

    if (Autoability.BREAK_HP_LIMIT in abilities
            and Autoability.BREAK_MP_LIMIT in abilities):
        index = 0
    elif Autoability.RIBBON in abilities:
        index = 1
    elif Autoability.BREAK_HP_LIMIT in abilities:
        index = 2
    elif Autoability.BREAK_MP_LIMIT in abilities:
        index = 3
    elif elemental_eaters == 4:
        index = 4
    elif elemental_proofs == 4:
        index = 5
    elif (Autoability.AUTO_SHELL in abilities
            and Autoability.AUTO_PROTECT in abilities
            and Autoability.AUTO_REFLECT in abilities
            and Autoability.AUTO_REGEN in abilities):
        index = 6
    elif (Autoability.AUTO_POTION in abilities
            and Autoability.AUTO_MED in abilities
            and Autoability.AUTO_PHOENIX in abilities):
        index = 7
    elif (Autoability.AUTO_POTION in abilities
            and Autoability.AUTO_MED in abilities):
        index = 8
    elif status_proofs == 4:
        index = 9
    elif defense_bonuses == 4:
        index = 10
    elif magic_def_bonuses == 4:
        index = 11
    elif hp_bonuses == 4:
        index = 12
    elif mp_bonuses == 4:
        index = 13
    elif Autoability.MASTER_THIEF in abilities:
        index = 14
    elif Autoability.PICKPOCKET in abilities:
        index = 15
    elif (Autoability.HP_STROLL in abilities
            and Autoability.MP_STROLL in abilities):
        index = 16
    elif auto_statuses == 3:
        index = 17
    elif elemental_eaters == 3:
        index = 18
    elif Autoability.HP_STROLL in abilities:
        index = 19
    elif Autoability.MP_STROLL in abilities:
        index = 20
    elif Autoability.AUTO_PHOENIX in abilities:
        index = 21
    elif Autoability.AUTO_MED in abilities:
        index = 22
    elif elemental_sos_auto_statuses == 4:
        index = 23
    elif status_soses == 4:
        index = 24
    elif status_proofs == 3:
        index = 25
    elif Autoability.NO_ENCOUNTERS in abilities:
        index = 26
    elif Autoability.AUTO_POTION in abilities:
        index = 27
    elif elemental_proofs == 3:
        index = 28
    elif status_soses == 3:
        index = 29
    elif auto_statuses == 2:
        index = 30
    elif elemental_sos_auto_statuses == 2:
        index = 31
    elif (Autoability.AUTO_REGEN in abilities
            or Autoability.SOS_REGEN in abilities):
        index = 32
    elif (Autoability.AUTO_HASTE in abilities
            or Autoability.SOS_HASTE in abilities):
        index = 33
    elif (Autoability.AUTO_REFLECT in abilities
            or Autoability.SOS_REFLECT in abilities):
        index = 34
    elif (Autoability.AUTO_SHELL in abilities
            or Autoability.SOS_SHELL in abilities):
        index = 35
    elif (Autoability.AUTO_PROTECT in abilities
            or Autoability.SOS_PROTECT in abilities):
        index = 36
    elif defense_bonuses == 3:
        index = 37
    elif magic_def_bonuses == 3:
        index = 38
    elif hp_bonuses == 3:
        index = 39
    elif mp_bonuses == 3:
        index = 40
    # TODO
    # this condition should not be true if the -eater and -proof abilities
    # are for the same element
    elif elemental_eaters + elemental_proofs >= 2:
        index = 41
    elif status_proofs == 2:
        index = 42
    elif Autoability.FIRE_EATER in abilities:
        index = 43
    elif Autoability.ICE_EATER in abilities:
        index = 44
    elif Autoability.LIGHTNING_EATER in abilities:
        index = 45
    elif Autoability.WATER_EATER in abilities:
        index = 46
    elif Autoability.CURSEPROOF in abilities:
        index = 47
    elif (Autoability.CONFUSE_WARD in abilities
            or Autoability.CONFUSEPROOF in abilities):
        index = 48
    elif (Autoability.BERSERK_WARD in abilities
            or Autoability.BERSERKPROOF in abilities):
        index = 49
    elif (Autoability.SLOW_WARD in abilities
            or Autoability.SLOWPROOF in abilities):
        index = 50
    elif (Autoability.DEATH_WARD in abilities
            or Autoability.DEATHPROOF in abilities):
        index = 51
    elif (Autoability.ZOMBIE_WARD in abilities
            or Autoability.ZOMBIEPROOF in abilities):
        index = 52
    elif (Autoability.STONE_WARD in abilities
            or Autoability.STONEPROOF in abilities):
        index = 53
    elif (Autoability.POISON_WARD in abilities
            or Autoability.POISONPROOF in abilities):
        index = 54
    elif (Autoability.SLEEP_WARD in abilities
            or Autoability.SLEEPPROOF in abilities):
        index = 55
    elif (Autoability.SILENCE_WARD in abilities
            or Autoability.SILENCEPROOF in abilities):
        index = 56
    elif (Autoability.DARK_WARD in abilities
            or Autoability.DARKPROOF in abilities):
        index = 57
    elif (Autoability.FIRE_WARD in abilities
            or Autoability.FIREPROOF in abilities):
        index = 58
    elif (Autoability.ICE_WARD in abilities
            or Autoability.ICEPROOF in abilities):
        index = 59
    elif (Autoability.LIGHTNING_WARD in abilities
            or Autoability.LIGHTNINGPROOF in abilities):
        index = 60
    elif (Autoability.WATER_WARD in abilities
            or Autoability.WATERPROOF in abilities):
        index = 61
    elif Autoability.SOS_NULTIDE in abilities:
        index = 62
    elif Autoability.SOS_NULBLAZE in abilities:
        index = 63
    elif Autoability.SOS_NULSHOCK in abilities:
        index = 64
    elif Autoability.SOS_NULFROST in abilities:
        index = 65
    elif hp_bonuses == 2 and mp_bonuses == 2:
        index = 66
    elif slots == 4:
        index = 67
    elif defense_bonuses >= 1 and magic_def_bonuses >= 1:
        index = 68
    elif defense_bonuses == 2:
        index = 69
    elif magic_def_bonuses == 2:
        index = 70
    elif hp_bonuses == 2:
        index = 71
    elif mp_bonuses == 2:
        index = 72
    elif (Autoability.DEFENSE_10 in abilities
            or Autoability.DEFENSE_20 in abilities):
        index = 73
    elif (Autoability.MAGIC_DEF_10 in abilities
            or Autoability.MAGIC_DEF_20 in abilities):
        index = 74
    elif (Autoability.MP_20 in abilities
            or Autoability.MP_30 in abilities):
        index = 75
    elif (Autoability.HP_20 in abilities
            or Autoability.HP_30 in abilities):
        index = 76
    elif slots == 3:
        index = 77
    elif (Autoability.DEFENSE_3 in abilities
            or Autoability.DEFENSE_5 in abilities):
        index = 78
    elif (Autoability.MAGIC_DEF_3 in abilities
            or Autoability.MAGIC_DEF_5 in abilities):
        index = 79
    elif (Autoability.MP_5 in abilities
            or Autoability.MP_10 in abilities):
        index = 80
    elif (Autoability.HP_5 in abilities
            or Autoability.HP_10 in abilities):
        index = 81
    elif slots == 2:
        index = 82
    elif slots == 1:
        index = 83
    else:
        index = 83

    return EQUIPMENT_NAMES[EquipmentType.ARMOR][index][owner]


EQUIPMENT_NAMES = _get_equipment_names('data_files/equipment_names.json')
