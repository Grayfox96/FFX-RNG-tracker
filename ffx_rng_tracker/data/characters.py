import json
from copy import deepcopy
from dataclasses import dataclass

from ..utils import open_cp1252
from .actions import ACTIONS
from .autoabilities import (AEON_RIBBON_IMMUNITIES, AUTO_STATUSES,
                            ELEMENTAL_EATERS, ELEMENTAL_PROOFS,
                            ELEMENTAL_SOS_AUTO_STATUSES, ELEMENTAL_STRIKES,
                            ELEMENTAL_WARDS, HP_BONUSES, MP_BONUSES,
                            RIBBON_IMMUNITIES, SOS_AUTO_STATUSES,
                            STATUS_PROOFS, STATUS_STRIKES, STATUS_TOUCHES,
                            STATUS_WARDS)
from .constants import (ICV_BASE, Autoability, Buff, Character, Element,
                        ElementalAffinity, EquipmentType, Stat, Status)
from .equipment import Equipment
from .file_functions import get_resource_path
from .statuses import StatusApplication


@dataclass(frozen=True)
class DefaultCharacterState:
    character: Character
    index: int
    starting_s_lv: int
    stats: dict[Stat, int]
    weapon: Equipment
    armor: Equipment


@dataclass
class CharacterState:
    defaults: DefaultCharacterState

    def __str__(self) -> str:
        return str(self.character)

    def __post_init__(self) -> None:
        self.armored = False
        self._weapon = Equipment(
            owner=self.character,
            type_=EquipmentType.WEAPON,
            slots=0,
            abilities=[],
            base_weapon_damage=16,
            bonus_crit=3,
        )
        self._armor = Equipment(
            owner=self.character,
            type_=EquipmentType.ARMOR,
            slots=0,
            abilities=[],
            base_weapon_damage=16,
            bonus_crit=0,
        )
        self.reset()

    @property
    def character(self) -> Character:
        return self.defaults.character

    @property
    def index(self) -> int:
        return self.defaults.index

    def set_stat(self, stat: Stat | Buff, value: int) -> None:
        match stat:
            case Stat.HP:
                max_value = 99999
            case Stat.MP:
                max_value = 9999
            case Buff():
                self.buffs[stat] = min(max(0, value), 5)
                return
            case _:
                max_value = 255
        value = min(max(0, value), max_value)
        self.stats[stat] = value
        if stat is Stat.HP and self.max_hp < self.current_hp:
            self.current_hp = self.max_hp
        elif stat is Stat.MP and self.max_hp < self.current_hp:
            self.current_mp = self.max_mp

    @property
    def ap(self) -> int:
        return self._ap

    @ap.setter
    def ap(self, value) -> None:
        self._ap = max(0, value)

    @property
    def s_lv(self) -> int:
        return total_ap_to_s_lv(self.ap, self.defaults.starting_s_lv)

    @property
    def max_hp(self) -> int:
        if self.break_hp_limit:
            max_value = 99999
        else:
            max_value = 9999
        max_hp = self.stats[Stat.HP] * self._hp_multiplier // 100
        if Status.MAX_HP_X_2 in self.statuses:
            max_hp = max_hp * 2
        return min(max_value, max_hp)

    @property
    def current_hp(self) -> int:
        return self._current_hp

    @current_hp.setter
    def current_hp(self, value: int) -> None:
        value = min(max(value, 0), self.max_hp)
        if value == 0:
            self.statuses[Status.DEATH] = 254
        self._current_hp = value

    @property
    def max_mp(self) -> int:
        if self.break_mp_limit:
            max_value = 9999
        else:
            max_value = 999
        max_mp = self.stats[Stat.MP] * self._mp_multiplier // 100
        if Status.MAX_MP_X_2 in self.statuses:
            max_mp = max_mp * 2
        return min(max_value, max_mp)

    @property
    def current_mp(self) -> int:
        return self._current_mp

    @current_mp.setter
    def current_mp(self, value) -> None:
        value = min(max(value, 0), self.max_mp)
        self._current_mp = value

    @property
    def base_ctb(self) -> int:
        return ICV_BASE[self.stats[Stat.AGILITY]]

    @property
    def ctb(self) -> int:
        return self._ctb

    @ctb.setter
    def ctb(self, value) -> None:
        self._ctb = max(0, value)

    @property
    def in_crit(self) -> bool:
        half_hp = self.max_hp / 2
        return self.current_hp < half_hp

    @property
    def dead(self) -> bool:
        dead = (self.current_hp == 0
                or Status.DEATH in self.statuses
                or Status.PETRIFY in self.statuses)
        return dead

    @property
    def inactive(self) -> bool:
        inactive = (Status.ESCAPE in self.statuses
                    or Status.EJECT in self.statuses)
        return inactive

    @property
    def weapon(self) -> Equipment:
        return self._weapon

    @weapon.setter
    def weapon(self, equipment: Equipment) -> None:
        self._weapon = equipment
        self._update_abilities_effects()

    @property
    def armor(self) -> Equipment:
        return self._armor

    @armor.setter
    def armor(self, equipment: Equipment) -> None:
        self._armor = equipment
        self._update_abilities_effects()

    @property
    def autoabilities(self) -> list[Autoability]:
        return self.weapon.abilities + self.armor.abilities

    def _update_abilities_effects(self) -> None:
        autoabilities = self.autoabilities
        self._hp_multiplier = 100
        self._mp_multiplier = 100
        self.elemental_affinities = dict.fromkeys(
            Element, ElementalAffinity.NEUTRAL)
        self.status_resistances = dict.fromkeys(Status, 0)
        self.status_resistances[Status.THREATEN] = 255
        self.equipment_elements: list[Element] = []
        self.status_strikes: list[StatusApplication] = []
        self.auto_statuses: list[Status] = []
        self.sos_auto_statuses: list[Status] = []
        self.first_strike = Autoability.FIRST_STRIKE in autoabilities
        self.break_hp_limit = Autoability.BREAK_HP_LIMIT in autoabilities
        self.break_mp_limit = Autoability.BREAK_MP_LIMIT in autoabilities
        for ability in autoabilities:
            if ability is Autoability.RIBBON:
                for status in RIBBON_IMMUNITIES:
                    self.status_resistances[status] = 255
            elif ability is Autoability.AEON_RIBBON:
                for status in AEON_RIBBON_IMMUNITIES:
                    self.status_resistances[status] = 255
            elif ability in ELEMENTAL_WARDS:
                element = ELEMENTAL_WARDS[ability]
                self.elemental_affinities[element] = ElementalAffinity.RESISTS
            elif ability in ELEMENTAL_PROOFS:
                element = ELEMENTAL_PROOFS[ability]
                self.elemental_affinities[element] = ElementalAffinity.IMMUNE
            elif ability in ELEMENTAL_EATERS:
                element = ELEMENTAL_EATERS[ability]
                self.elemental_affinities[element] = ElementalAffinity.ABSORBS
            elif ability in STATUS_PROOFS:
                status = STATUS_PROOFS[ability]
                self.status_resistances[status] = 255
            elif ability in STATUS_WARDS:
                status = STATUS_WARDS[ability]
                self.status_resistances[status] = max(
                    self.status_resistances[status], 50)
            elif ability in HP_BONUSES:
                self._hp_multiplier += HP_BONUSES[ability]
            elif ability in MP_BONUSES:
                self._mp_multiplier += MP_BONUSES[ability]
            elif ability in ELEMENTAL_STRIKES:
                self.equipment_elements.append(ELEMENTAL_STRIKES[ability])
            elif ability in STATUS_TOUCHES:
                self.status_strikes.append(STATUS_TOUCHES[ability])
            elif ability in STATUS_STRIKES:
                self.status_strikes.append(STATUS_STRIKES[ability])
            elif ability in AUTO_STATUSES:
                self.auto_statuses.append(AUTO_STATUSES[ability])
            elif ability in SOS_AUTO_STATUSES or ability in ELEMENTAL_SOS_AUTO_STATUSES:
                self.sos_auto_statuses.append(ability)

    def reset(self) -> None:
        self.ap = 0
        self.stats = self.defaults.stats.copy()
        self.ctb = 0
        self.buffs: dict[Buff, int] = dict.fromkeys(Buff, 0)
        self._current_hp = self.stats[Stat.HP]
        self._current_mp = self.stats[Stat.MP]
        self.statuses: dict[Status, int] = {}
        self.weapon = deepcopy(self.defaults.weapon)
        self.armor = deepcopy(self.defaults.armor)
        self.last_action = ACTIONS['does_nothing']


def _get_characters(file_path: str) -> dict[Character, DefaultCharacterState]:
    """"""
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data: dict = json.load(file_object)
    characters = {}
    for character, character_data in data.items():
        character = Character(character)
        weapon_data = character_data['weapon']
        weapon = Equipment(
            owner=character,
            type_=EquipmentType.WEAPON,
            slots=weapon_data['slots'],
            abilities=[Autoability(a) for a in weapon_data['abilities']],
            base_weapon_damage=weapon_data['base_weapon_damage'],
            bonus_crit=weapon_data['bonus_crit'],
        )
        armor_data = character_data['armor']
        armor = Equipment(
            owner=character,
            type_=EquipmentType.ARMOR,
            slots=armor_data['slots'],
            abilities=[Autoability(a) for a in armor_data['abilities']],
            base_weapon_damage=16,
            bonus_crit=armor_data['bonus_crit'],
        )
        characters[character] = DefaultCharacterState(
            character=character,
            index=character_data['index'],
            starting_s_lv=character_data['starting_s_lv'],
            stats={Stat(k): v for k, v in character_data['stats'].items()},
            weapon=weapon,
            armor=armor,
        )

    return characters


def s_lv_to_ap(s_lv: int) -> int:
    """Returns the AP needed for a specific Sphere Level."""
    ap = int(5 * (s_lv + 1)) + int((s_lv ** 3) / 50)
    return min(ap, 22000)


def total_ap_to_s_lv(ap_total: int, starting_s_lv: int = 0) -> int:
    """Returns the Sphere Level reached with the given amount of AP."""
    ap = 0
    s_lv = 0
    while True:
        if ap_total < ap:
            return s_lv - 1
        ap += s_lv_to_ap(s_lv + starting_s_lv)
        s_lv += 1


def s_lv_to_total_ap(s_lv: int, starting_s_lv: int = 0) -> int:
    """Returns the AP needed to reach a specific Sphere Level."""
    return sum([s_lv_to_ap(i + starting_s_lv) for i in range(s_lv)])


def calculate_power_base(stats: dict[Stat, int]) -> int:
    power_base = ((min(stats[Stat.HP], 9999) // 100)
                  + (min(stats[Stat.MP], 999) // 10)
                  + stats[Stat.STRENGTH]
                  + stats[Stat.DEFENSE]
                  + stats[Stat.MAGIC]
                  + stats[Stat.MAGIC_DEFENSE]
                  + stats[Stat.AGILITY]
                  + stats[Stat.EVASION]
                  + stats[Stat.ACCURACY]
                  )
    return power_base


CHARACTERS_DEFAULTS = _get_characters('data_files/characters.json')
