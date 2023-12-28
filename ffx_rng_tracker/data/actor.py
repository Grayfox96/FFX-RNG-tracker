from copy import deepcopy
from dataclasses import dataclass
from typing import Protocol, Self

from .actions import Action
from .autoabilities import (AEON_RIBBON_IMMUNITIES, AUTO_STATUSES,
                            ELEMENTAL_EATERS, ELEMENTAL_PROOFS,
                            ELEMENTAL_SOS_AUTO_STATUSES, ELEMENTAL_STRIKES,
                            ELEMENTAL_WARDS, HP_BONUSES, MP_BONUSES,
                            RIBBON_IMMUNITIES, SOS_AUTO_STATUSES,
                            STATUS_PROOFS, STATUS_STRIKES, STATUS_TOUCHES,
                            STATUS_WARDS)
from .characters import DefaultCharacterState, total_ap_to_s_lv
from .constants import (ICV_BASE, Autoability, Buff, Element,
                        ElementalAffinity, MonsterSlot, Stat, Status)
from .equipment import Equipment
from .monsters import Monster
from .statuses import StatusApplication


class Actor(Protocol):
    index: int
    max_hp: int
    current_hp: int
    max_mp: int
    current_mp: int
    base_ctb: int
    ctb: int
    armored: bool
    immune_to_damage: bool
    immune_to_physical_damage: bool
    immune_to_magical_damage: bool
    immune_to_percentage_damage: bool
    immune_to_delay: bool
    immune_to_life: bool
    stats: dict[Stat, int]
    buffs: dict[Buff, int]
    statuses: dict[Status, int]
    status_resistances: dict[Status, int]
    elemental_affinities: dict[Element, ElementalAffinity]
    base_weapon_damage: int
    equipment_crit: int
    autoabilities: list[Autoability]
    weapon_elements: list[Element]
    weapon_statuses: list[StatusApplication]
    last_action: Action | None
    provoker: Self | None
    last_attacker: Self | None
    last_target: list[Self]

    def set_stat(self, stat: Stat | Buff, value: int) -> None:
        """Sets the stat to the value, clamping to the
        appropriate min and max values
        """


class CharacterActor:
    def __init__(self, defaults: DefaultCharacterState) -> None:
        self.defaults = defaults
        self.index = defaults.index
        self.character = defaults.character
        self.armored = False
        self.immune_to_damage = False
        self.immune_to_physical_damage = False
        self.immune_to_magical_damage = False
        self.immune_to_percentage_damage = False
        self.immune_to_delay = False
        self.immune_to_life = False
        self.reset()

    def __str__(self) -> str:
        return self.character

    def reset(self) -> None:
        self.ap = 0
        self.stats = self.defaults.stats.copy()
        self.ctb = 0
        self.buffs = dict.fromkeys(Buff, 0)
        self._current_hp = self.stats[Stat.HP]
        self._current_mp = self.stats[Stat.MP]
        self.statuses: dict[Status, int] = {}
        self.in_crit = False
        self._weapon = deepcopy(self.defaults.weapon)
        self._armor = deepcopy(self.defaults.armor)
        self._update_abilities_effects()
        self.last_action = None
        self.provoker: Actor | None = None
        self.last_attacker: Actor | None = None
        self.last_target: list[Actor] = []

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
        elif stat is Stat.MP and self.max_mp < self.current_mp:
            self.current_mp = self.max_mp

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
        max_hp = self.max_hp
        value = min(max(value, 0), max_hp)
        if value == 0:
            self.statuses[Status.DEATH] = 254
        self.in_crit = value < (max_hp / 2)
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
    def ap(self) -> int:
        return self._ap

    @ap.setter
    def ap(self, value) -> None:
        self._ap = max(0, value)

    @property
    def s_lv(self) -> int:
        return total_ap_to_s_lv(self.ap, self.defaults.starting_s_lv)

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

    def _update_abilities_effects(self) -> None:
        self.base_weapon_damage = self.weapon.base_weapon_damage
        self.equipment_crit = self.weapon.bonus_crit + self.armor.bonus_crit
        self.autoabilities = self.weapon.abilities + self.armor.abilities
        self._hp_multiplier = 100
        self._mp_multiplier = 100
        self.elemental_affinities = dict.fromkeys(
            Element, ElementalAffinity.NEUTRAL)
        self.status_resistances = dict.fromkeys(Status, 0)
        self.status_resistances[Status.THREATEN] = 255
        self.weapon_elements: list[Element] = []
        self.weapon_statuses: list[StatusApplication] = []
        self.auto_statuses: list[Status] = []
        self.sos_auto_statuses: list[Status] = []
        self.first_strike = Autoability.FIRST_STRIKE in self.autoabilities
        self.break_hp_limit = Autoability.BREAK_HP_LIMIT in self.autoabilities
        self.break_mp_limit = Autoability.BREAK_MP_LIMIT in self.autoabilities
        for ability in self.autoabilities:
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
                self.weapon_elements.append(ELEMENTAL_STRIKES[ability])
            elif ability in STATUS_TOUCHES:
                self.weapon_statuses.append(STATUS_TOUCHES[ability])
            elif ability in STATUS_STRIKES:
                self.weapon_statuses.append(STATUS_STRIKES[ability])
            elif ability in AUTO_STATUSES:
                self.auto_statuses.append(AUTO_STATUSES[ability])
            elif (ability in SOS_AUTO_STATUSES
                    or ability in ELEMENTAL_SOS_AUTO_STATUSES):
                self.sos_auto_statuses.append(ability)


class MonsterActor:
    def __init__(self,
                 monster: Monster,
                 index: MonsterSlot = MonsterSlot.MONSTER_1,
                 ) -> None:
        self.monster = monster
        self.index = index
        self.equipment_crit = 0
        self.weapon_elements = []
        self.autoabilities = []
        self.weapon_statuses = []
        self.armored = monster.armored
        self.immune_to_damage = monster.immune_to_damage
        self.immune_to_physical_damage = monster.immune_to_physical_damage
        self.immune_to_magical_damage = monster.immune_to_magical_damage
        self.immune_to_percentage_damage = monster.immune_to_percentage_damage
        self.immune_to_delay = monster.immune_to_delay
        self.immune_to_life = monster.immune_to_life
        self.reset()

    def __str__(self) -> str:
        return f'{self.monster} (M{self.index + 1})'

    def reset(self) -> None:
        self.stats = self.monster.stats.copy()
        self.ctb = 0
        self.buffs = dict.fromkeys(Buff, 0)
        self._current_hp = self.stats[Stat.HP]
        self._current_mp = self.stats[Stat.MP]
        self.statuses: dict[Status, int] = {}
        self.elemental_affinities = self.monster.elemental_affinities.copy()
        self.status_resistances = self.monster.status_resistances.copy()
        self.last_action = None
        self.provoker: Actor | None = None
        self.last_attacker: Actor | None = None
        self.last_target: list[Actor] = []

    def set_stat(self, stat: Stat | Buff, value: int) -> None:
        match stat:
            case Stat.HP | Stat.MP:
                pass
            case Buff():
                self.buffs[stat] = min(max(0, value), 5)
                return
            case _:
                value = min(value, 255)
        self.stats[stat] = max(0, value)
        if stat is Stat.HP and self.max_hp < self.current_hp:
            self.current_hp = self.max_hp
        elif stat is Stat.MP and self.max_mp < self.current_mp:
            self.current_mp = self.max_mp

    @property
    def max_hp(self) -> int:
        return self.stats[Stat.HP]

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
        return self.stats[Stat.MP]

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
