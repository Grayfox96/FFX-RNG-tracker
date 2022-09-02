from dataclasses import dataclass, field

from ..data.actions import Action
from ..data.autoabilities import (ELEMENTAL_STRIKES, MAGIC_BONUSES,
                                  STATUS_STRIKES, STATUS_TOUCHES,
                                  STRENGTH_BONUSES)
from ..data.characters import CharacterState
from ..data.constants import (ELEMENTAL_AFFINITY_MODIFIERS, HIT_CHANCE_TABLE,
                              ICV_BASE, NO_RNG_STATUSES, TEMPORARY_STATUSES,
                              Autoability, DamageType, ElementalAffinity, Stat,
                              Status)
from ..data.monsters import Monster
from .main import Event


@dataclass
class CharacterAction(Event):
    character: CharacterState
    action: Action
    target: CharacterState | Monster
    hit: bool = field(init=False, repr=False)
    statuses: dict[Status, bool] = field(init=False, repr=False)
    damage: int = field(init=False, repr=False)
    damage_rng: int = field(init=False, repr=False)
    crit: bool = field(init=False, repr=False)
    ctb: int = field(init=False, repr=False)
    _old_statuses: set[Status] = field(
        default_factory=set, init=False, repr=False)
    _old_target_hp: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._old_statuses = self._remove_temporary_statuses()
        self.hit = self._get_hit()
        self.statuses = self._get_statuses()
        self.damage_rng = self._get_damage_rng()
        self.crit = self._get_crit()
        self.damage = self._get_damage()
        self.ctb = self._get_ctb()

    def __str__(self) -> str:
        string = (f'{self.character} -> {self.action}'
                  f' [{self.ctb}]'
                  f' -> {self.target}:')
        if self.hit:
            if self.action.does_damage:
                string += f' [{self.damage_rng}/31]'
                string += f' {self.damage}'
                if self.crit:
                    string += ' (Crit)'
            else:
                string += ' (No damage)'
            if self.statuses:
                string += ' '
                statuses = []
                for status, applied in self.statuses.items():
                    if applied:
                        statuses.append(f'[{status}]')
                    else:
                        statuses.append(f'[{status} Fail]')
                string += ' '.join(statuses)
        else:
            string += ' Miss'
        return string

    def _remove_temporary_statuses(self) -> set[Status]:
        statuses = self.character.statuses.copy()
        self.character.statuses.difference_update(TEMPORARY_STATUSES)
        return statuses

    def _get_hit(self) -> bool:
        if not self.action.can_miss:
            return True
        index = min(36 + self.character.index, 43)
        hit_rng = self._advance_rng(index) % 101
        luck = self.character.stats[Stat.LUCK]
        accuracy = self.character.stats[Stat.ACCURACY]
        target_evasion = self.target.stats[Stat.EVASION]
        target_luck = max(self.target.stats[Stat.LUCK], 1)
        # TODO
        aims = 0
        target_reflexes = 0
        hit_chance = accuracy * 2
        hit_chance = (hit_chance * 0x66666667) // 0xffffffff
        hit_chance = hit_chance // 2
        hit_chance_index = hit_chance // 0x80000000
        hit_chance_index += hit_chance - target_evasion + 10
        if hit_chance_index < 0:
            hit_chance_index = 0
        elif hit_chance_index > 8:
            hit_chance_index = 8
        base_hit_chance = HIT_CHANCE_TABLE[hit_chance_index]
        if Status.DARK in self.character.statuses:
            base_hit_chance = (base_hit_chance * 0x66666667) // 0xffffffff
            base_hit_chance = base_hit_chance // 4
        hit_chance = base_hit_chance + luck
        hit_chance += (aims - target_reflexes) * 10 - target_luck
        return hit_chance > hit_rng

    def _get_damage_rng(self) -> int:
        if not self.hit or not self.action.does_damage:
            return 0
        index = min(20 + self.character.index, 27)
        return self._advance_rng(index) & 31

    def _get_crit(self) -> bool:
        if (not self.hit
                or not self.action.does_damage
                or not self.action.can_crit):
            return False
        index = min(20 + self.character.index, 27)
        crit_roll = self._advance_rng(index) % 101
        luck = self.character.stats[Stat.LUCK]
        target_luck = max(self.target.stats[Stat.LUCK], 1)
        crit_chance = luck - target_luck
        if self.action.uses_weapon:
            crit_chance += self.character.weapon.bonus_crit
            crit_chance += self.character.armor.bonus_crit
        return crit_roll < crit_chance

    def _get_damage(self) -> int:
        if not self.hit or not self.action.does_damage:
            return 0
        damage = get_damage(
            self.character, self.action, self.target, self.damage_rng,
            self.crit)
        if isinstance(self.target, CharacterState):
            self._old_target_hp = self.target.current_hp
            self.target.current_hp -= damage
        return damage

    def _get_statuses(self) -> dict[Status, bool]:
        if not self.hit:
            return {}
        index = min(52 + self.character.index, 59)
        statuses_applied = {}
        statuses = self.action.statuses.copy()
        for status in statuses:
            if status in (Status.HASTE, Status.SLOW):
                self._advance_rng(min(20 + self.character.index, 27))
        if self.action.uses_weapon:
            for ability in self.character.autoabilities:
                if ability in STATUS_TOUCHES:
                    status = STATUS_TOUCHES[ability]
                    status_chance = 50
                elif ability in STATUS_STRIKES:
                    status = STATUS_STRIKES[ability]
                    status_chance = 100
                else:
                    continue
                statuses[status] = max(status_chance, statuses.get(status, 0))
        for status, chance in statuses.items():
            if status in NO_RNG_STATUSES:
                status_rng = 0
            else:
                status_rng = self._advance_rng(index) % 101
            resistance = self.target.status_resistances.get(status, 0)
            if chance == 255:
                applied = True
            elif resistance == 255:
                applied = False
            elif chance == 254:
                applied = True
            elif (chance - resistance) > status_rng:
                applied = True
            else:
                applied = False
            if applied and isinstance(self.target, CharacterState):
                self.target.statuses.add(status)
            statuses_applied[status] = applied
            if status is Status.PETRIFY and applied:
                # advance rng once more for shatter
                self._advance_rng(index)
        return statuses_applied

    def _get_ctb(self) -> int:
        rank = self.action.rank
        ctb_base = ICV_BASE[self.character.stats[Stat.AGILITY]]
        ctb = ctb_base * rank
        if (Status.HASTE in self.character.statuses
                or Autoability.AUTO_HASTE in self.character.autoabilities
                or (Autoability.SOS_HASTE in self.character.autoabilities
                    and self.character.in_crit)):
            ctb = ctb // 2
        elif Status.SLOW in self.character.statuses:
            ctb = ctb * 2
        return ctb

    def rollback(self) -> None:
        if isinstance(self.target, CharacterState):
            self.target.current_hp = self._old_target_hp
        self.character.statuses = self._old_statuses
        return super().rollback()


def get_damage(
        user: CharacterState | Monster,
        action: Action,
        target: CharacterState | Monster,
        damage_rng: int,
        crit: bool,
        ) -> int:
    user_is_character = isinstance(user, CharacterState)
    target_is_character = isinstance(target, CharacterState)
    variance = damage_rng + 0xf0
    damage_type = action.damage_type
    element_mods = [-1.0]
    if action.element:
        affinity = target.elemental_affinities[action.element]
        element_mods[0] = ELEMENTAL_AFFINITY_MODIFIERS[affinity]
    elif action.uses_weapon and user_is_character:
        elemental_strikes = 0
        # if more than 1 elemental strike then only the stronger one applies
        # unless the target is weak to more than one then apply them all
        for ability in user.autoabilities:
            if ability not in ELEMENTAL_STRIKES:
                continue
            elemental_strikes += 1
            element = ELEMENTAL_STRIKES[ability]
            affinity = target.elemental_affinities[element]
            if element_mods[0] == 1.5 and affinity is ElementalAffinity.WEAK:
                element_mods.append(ELEMENTAL_AFFINITY_MODIFIERS[affinity])
            else:
                element_mods[0] = max(
                    element_mods[0], ELEMENTAL_AFFINITY_MODIFIERS[affinity])
        if elemental_strikes == 0:
            element_mods[0] = 1.0
    else:
        element_mods[0] = 1.0
    # special cases where the damage formula
    # is a lot less complicated
    if damage_type == DamageType.ITEM:
        damage = action.base_damage * 50
        damage = damage * variance // 256
        if crit:
            damage = damage * 2
        for element_mod in element_mods:
            damage = int(damage * element_mod)
        return damage
    elif damage_type == DamageType.FIXED:
        damage = action.base_damage
        return damage
    elif damage_type is DamageType.PERCENTAGE_TOTAL:
        if target_is_character:
            hp = target.max_hp
        else:
            hp = target.stats[Stat.HP]
        damage = hp * action.base_damage // 16
        return damage
    elif damage_type is DamageType.PERCENTAGE_CURRENT:
        if target_is_character:
            hp = target.current_hp
        else:
            hp = target.stats[Stat.HP]
        damage = hp * action.base_damage // 16
        return damage
    elif damage_type == DamageType.HP:
        if user_is_character:
            hp = user.max_hp
        else:
            hp = user.stats[Stat.HP]
        damage = hp * action.base_damage // 100
        if crit:
            damage = int(damage * 2)
        return damage
    elif damage_type == DamageType.GIL:
        damage = 0  # damage = gil/10
        return damage

    if damage_type in (DamageType.STRENGTH, DamageType.SPECIAL_STRENGTH):
        if action.uses_weapon:
            base_damage = user.weapon.base_weapon_damage
        else:
            base_damage = action.base_damage
        offensive_stat = user.stats[Stat.STRENGTH]
        offensive_stat += user.stats.get(Stat.CHEER, 0)
        defensive_buffs = target.stats.get(Stat.CHEER, 0)
        bonus = 0
        if user_is_character:
            for ability in user.autoabilities:
                bonus += STRENGTH_BONUSES.get(ability, 0)
        defensive_stat = max(target.stats[Stat.DEFENSE], 1)
    elif damage_type in (DamageType.MAGIC, DamageType.SPECIAL_MAGIC,
                         DamageType.HEALING):
        base_damage = action.base_damage
        offensive_stat = user.stats[Stat.MAGIC]
        offensive_stat += user.stats.get(Stat.FOCUS, 0)
        defensive_buffs = target.stats.get(Stat.FOCUS, 0)
        bonus = 0
        if user_is_character:
            for ability in user.autoabilities:
                bonus += MAGIC_BONUSES.get(ability, 0)
        if action.damage_type == DamageType.MAGIC:
            defensive_stat = max(target.stats[Stat.MAGIC_DEFENSE], 1)
        else:
            defensive_stat = 0
    if damage_type in (DamageType.STRENGTH, DamageType.SPECIAL_STRENGTH,
                       DamageType.SPECIAL_MAGIC):
        power = offensive_stat * offensive_stat * offensive_stat
        power = (power // 0x20) + 0x1e
    elif damage_type in (DamageType.MAGIC, DamageType.HEALING):
        power = offensive_stat * offensive_stat
        power = (power * 0x2AAAAAAB) // 0xffffffff
        power = power + (power // 0x80000000)
        power = (power + base_damage) * base_damage
        power = power // 4
    mitigation_1 = defensive_stat * defensive_stat
    mitigation_1 = (mitigation_1 * 0x2E8BA2E9) // 0xffffffff
    mitigation_1 = mitigation_1 // 2
    mitigation_1 = mitigation_1 + (mitigation_1 // 0x80000000)
    mitigation_2 = defensive_stat * 0x33
    mitigation = mitigation_2 - mitigation_1
    mitigation = (mitigation * 0x66666667) // 0xffffffff
    mitigation = mitigation // 4
    mitigation = mitigation + (mitigation // 0x80000000)
    mitigation = 0x2da - mitigation
    if damage_type is DamageType.HEALING:
        defensive_buffs = 0
    damage_1 = power * mitigation
    damage_2 = (damage_1 * -1282606671) // 0xffffffff
    damage_3 = damage_2 + damage_1
    damage_3 = damage_3 // 0x200
    damage_3 = damage_3 * (15 - defensive_buffs)
    damage_4 = (damage_3 * -2004318071) // 0xffffffff
    damage = (damage_4 + damage_3) // 0x8
    damage = damage + (damage // 0x80000000)
    if damage_type in (DamageType.STRENGTH, DamageType.SPECIAL_STRENGTH,
                       DamageType.SPECIAL_MAGIC):
        damage = damage * base_damage // 0x10
    damage = damage * variance // 0x100
    if crit:
        damage = damage * 2
    for element_mod in element_mods:
        damage = int(damage * element_mod)
    if damage_type is DamageType.STRENGTH:
        if target_is_character:
            if Status.DEFEND in target.statuses:
                damage = damage // 2
        elif (target.armored
                and user_is_character
                and Autoability.PIERCING not in user.autoabilities):
            damage = damage // 3
    damage = damage + (damage * bonus // 100)
    damage = int(damage)
    if damage_type == DamageType.HEALING:
        damage = damage * -1
    if target_is_character:
        if Status.BOOST in target.statuses:
            damage = int(damage * 1.5)
        elif Status.SHIELD in target.statuses:
            damage = damage // 4
    if user_is_character:
        if Autoability.BREAK_DAMAGE_LIMIT in user.autoabilities:
            damage_limit = 99999
        else:
            damage_limit = 9999
    else:
        damage_limit = 99999
    damage = min(damage, damage_limit)
    return damage
