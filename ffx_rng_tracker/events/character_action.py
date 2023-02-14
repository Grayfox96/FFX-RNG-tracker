from dataclasses import dataclass

from ..data.actions import Action
from ..data.autoabilities import (DEFENSE_BONUSES, MAGIC_BONUSES,
                                  MAGIC_DEF_BONUSES, STRENGTH_BONUSES)
from ..data.characters import CharacterState
from ..data.constants import (ELEMENTAL_AFFINITY_MODIFIERS, HIT_CHANCE_TABLE,
                              Autoability, Buff, DamageType, Element,
                              ElementalAffinity, Stat, Status)
from ..data.monsters import MonsterState
from ..data.statuses import NO_RNG_STATUSES, NUL_STATUSES
from .main import Event


@dataclass
class CharacterAction(Event):
    character: CharacterState
    action: Action
    target: CharacterState | MonsterState
    time_remaining: int = 0

    def __post_init__(self) -> None:
        self.gamestate.process_start_of_turn(self.character)
        self.hit = self._get_hit()
        self.statuses = self._get_statuses()
        self.removed_statuses = self._remove_statuses()
        self.buffs = self._get_buffs()
        self.damage_rng = self._get_damage_rng()
        self.crit = self._get_crit()
        self.damage = self._get_damage()
        self.ctb = self._get_ctb()
        self.gamestate.process_end_of_turn(self.character)

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
                string += ''.join(statuses)
            if self.removed_statuses:
                string += ' '
                statuses = [f'[-{s}]' for s in self.removed_statuses]
                string += ''.join(statuses)
            if self.buffs:
                string += ' '
                buffs = [f'[{b} {a}]' for b, a in self.buffs.items()]
                string += ' '.join(buffs)
        else:
            string += ' Miss'
        return string

    def _get_hit(self) -> bool:
        if not self.action.can_miss:
            return True
        index = min(36 + self.character.index, 43)
        hit_rng = self._advance_rng(index) % 101
        luck = self.character.stats[Stat.LUCK]
        accuracy = self.character.stats[Stat.ACCURACY]
        target_evasion = self.target.stats[Stat.EVASION]
        target_luck = max(self.target.stats[Stat.LUCK], 1)
        aims = self.character.buffs[Buff.AIM]
        target_reflexes = self.target.buffs[Buff.REFLEX]
        hit_chance = accuracy * 2
        hit_chance = (hit_chance * 0x66666667) // 0xffffffff
        hit_chance = hit_chance // 2
        hit_chance_index = hit_chance // 0x80000000
        hit_chance_index += hit_chance - target_evasion + 10
        hit_chance_index = min(max(0, hit_chance_index), 8)
        base_hit_chance = HIT_CHANCE_TABLE[hit_chance_index]
        # TODO
        # add a "affected_by_dark" property to Action
        if Status.DARK in self.character.statuses:
            base_hit_chance = base_hit_chance * 0x66666667 // 0xffffffff
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
        if Status.CRITICAL in self.character.statuses:
            return True
        luck = self.character.stats[Stat.LUCK]
        luck += self.character.buffs[Buff.LUCK] * 10
        target_luck = max(self.target.stats[Stat.LUCK], 1)
        target_luck -= self.target.buffs[Buff.JINX] * 10
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
            self.crit, self.time_remaining)
        if self.action.damages_mp:
            self.target.current_mp -= damage
            if self.action.drains:
                self.character.current_mp += damage
        elif self.action.damage_type is DamageType.CTB:
            self.target.ctb -= damage
        else:
            self.target.current_hp -= damage
            if self.action.drains:
                self.character.current_hp += damage
        return damage

    def _get_statuses(self) -> dict[Status, bool]:
        if not self.hit:
            return {}
        index = min(52 + self.character.index, 59)
        statuses_applied: dict[Status, bool] = {}
        statuses = self.action.statuses.copy()
        if self.action.uses_weapon:
            for application in self.character.status_strikes:
                if application.status in statuses:
                    if application.chance > statuses[application.status].chance:
                        statuses[application.status] = application
                else:
                    statuses[application.status] = application
        for status, application in statuses.items():
            if status in NO_RNG_STATUSES:
                status_rng = 0
            else:
                status_rng = self._advance_rng(index) % 101
            resistance = self.target.status_resistances.get(status, 0)
            if application.chance == 255:
                applied = True
            elif resistance == 255:
                applied = False
            elif application.chance == 254:
                applied = True
            elif (application.chance - resistance) > status_rng:
                applied = True
            else:
                applied = False
            statuses_applied[status] = applied
            if not applied:
                continue
            if status is Status.DELAY_WEAK:
                self.target.ctb += self.target.base_ctb * 3 // 2
                continue
            elif status is Status.DELAY_STRONG:
                self.target.ctb += self.target.base_ctb * 3
                continue
            elif status is Status.HASTE:
                if self.target.statuses.get(Status.SLOW, 0) >= 255:
                    continue
                self.target.statuses.pop(Status.SLOW, None)
            elif status is Status.SLOW:
                if self.target.statuses.get(Status.HASTE, 0) >= 255:
                    continue
                self.target.statuses.pop(Status.HASTE, None)
            self.target.statuses[status] = application.stacks
        if Status.PETRIFY in self.target.statuses:
            # advance for shatter chance
            self._advance_rng(index)
            # TODO
            # if the target is a monster every action shatters
            # if the target is a character?
            self.target.statuses[Status.DEATH] = 254
            self.target.statuses.pop(Status.PETRIFY)
            statuses_applied[Status.DEATH] = True
        return statuses_applied

    def _remove_statuses(self) -> list[Status]:
        removed_statuses = []
        for status in self.action.dispels:
            if status not in self.target.statuses:
                continue
            if self.target.statuses[status] >= 255:
                continue
            removed_status = self.target.statuses.pop(status)
            if removed_status is Status.DEATH:
                self.target.ctb = self.target.base_ctb * 3
            removed_statuses.append(removed_status)
        return removed_statuses

    def _get_buffs(self) -> dict[Buff, int]:
        if not self.hit:
            return {}
        buffs = {}
        for buff, amount in self.action.buffs.items():
            self.target.buffs[buff] += amount
            buffs[buff] = self.target.buffs[buff]
        return buffs

    def _get_ctb(self) -> int:
        rank = self.action.rank
        ctb = self.character.base_ctb * rank
        if Status.HASTE in self.character.statuses:
            ctb = ctb // 2
        elif Status.SLOW in self.character.statuses:
            ctb = ctb * 2
        self.character.ctb += ctb
        return ctb


def get_damage(
        user: CharacterState | MonsterState,
        action: Action,
        target: CharacterState | MonsterState,
        damage_rng: int = 0,
        crit: bool = False,
        time_remaining: int = 0,
        ) -> int:
    user_is_character = isinstance(user, CharacterState)
    target_is_character = isinstance(target, CharacterState)
    variance = damage_rng + 0xf0
    damage_type = action.damage_type
    elements: set[Element] = set()
    if action.element:
        elements.add(action.element)
    if action.uses_weapon and user_is_character:
        elements.update(user.equipment_elements)
    if elements:
        element_mods = [-1.0]
        # check if all the elements are covered by a nul-status
        nul_statuses = set()
        for element in elements:
            status = NUL_STATUSES[element]
            if status in target.statuses:
                nul_statuses.add(status)
        # if they are, target is immune and decrease
        # the amount of status stacks by 1
        if len(elements) == len(nul_statuses):
            for nul_status in nul_statuses:
                if target.statuses[nul_status] >= 254:
                    continue
                target.statuses[nul_status] -= 1
                if target.statuses[nul_status] <= 0:
                    del target.statuses[nul_status]
            element_mods = [0.0]
        # otherwise check other element affinities normally
        else:
            # if more than 1 element then only the stronger one applies
            # unless the target is weak to more
            # than one then apply all of those
            for element in elements:
                affinity = target.elemental_affinities[element]
                if element_mods[0] == 1.5 and affinity is ElementalAffinity.WEAK:
                    element_mods.append(ELEMENTAL_AFFINITY_MODIFIERS[affinity])
                else:
                    element_mods[0] = max(
                        element_mods[0],
                        ELEMENTAL_AFFINITY_MODIFIERS[affinity])
    else:
        element_mods = [1.0]

    # special cases where the damage formula
    # is a lot less complicated
    if damage_type is DamageType.ITEM:
        damage = action.base_damage * 50
        damage = damage * variance // 256
        if crit:
            damage = damage * 2
        for element_mod in element_mods:
            damage = int(damage * element_mod)
        if action.damages_mp:
            damage = min(damage, target.current_mp)
        return damage
    elif damage_type == DamageType.FIXED:
        damage = action.base_damage
        return damage
    elif damage_type is DamageType.PERCENTAGE_TOTAL:
        hp = target.max_hp
        damage = hp * action.base_damage // 16
        return damage
    elif damage_type is DamageType.PERCENTAGE_CURRENT:
        hp = target.current_hp
        damage = hp * action.base_damage // 16
        return damage
    elif damage_type == DamageType.HP:
        hp = user.max_hp
        damage = hp * action.base_damage // 100
        if crit:
            damage = int(damage * 2)
        return damage
    elif damage_type is DamageType.GIL:
        # TODO
        # find a better way to calculate this
        # damage = gil // 10
        # hijacking the time_remaining parameter, diving by 1000 because
        # it normally represents milliseconds
        damage_limit = 9999
        damage = (time_remaining // 1000) // 10
        damage = min(damage, damage_limit)
        return damage
    elif damage_type is DamageType.CTB:
        damage = target.ctb * action.base_damage // 16
        return damage
    elif damage_type is DamageType.HEALING:
        base_damage = action.base_damage
        magic = user.stats[Stat.MAGIC] + user.buffs[Buff.FOCUS]
        bonus = 100
        if user_is_character:
            for ability in user.autoabilities:
                bonus += MAGIC_BONUSES.get(ability, 0)
        damage = (magic + base_damage) // 2 * variance * base_damage // 256
        if Status.SHELL in target.statuses:
            damage = damage // 2
        if Status.MAGIC_BREAK in user.statuses:
            damage = damage // 2
        damage = damage * bonus // 100
        if Status.ZOMBIE not in target.statuses:
            damage = damage * -1
        return damage

    if damage_type in (DamageType.STRENGTH, DamageType.SPECIAL_STRENGTH):
        if action.base_damage:
            base_damage = action.base_damage
        elif user_is_character and action.uses_weapon:
            base_damage = user.weapon.base_weapon_damage
        else:
            base_damage = 0
        offensive_stat = user.stats[Stat.STRENGTH]
        offensive_stat += user.buffs[Buff.CHEER]
        defensive_buffs = target.buffs[Buff.CHEER]
        offensive_bonus = 0
        defensive_bonus = 0
        if user_is_character and action.uses_weapon:
            for ability in user.autoabilities:
                offensive_bonus += STRENGTH_BONUSES.get(ability, 0)
        if target_is_character:
            for ability in target.autoabilities:
                defensive_bonus += DEFENSE_BONUSES.get(ability, 0)
        if Status.ARMOR_BREAK not in target.statuses:
            defensive_stat = max(target.stats[Stat.DEFENSE], 1)
        else:
            defensive_stat = 0
    else:  # MAGIC or SPECIAL_MAGIC
        base_damage = action.base_damage
        offensive_stat = user.stats[Stat.MAGIC]
        offensive_stat += user.buffs[Buff.FOCUS]
        defensive_buffs = target.buffs[Buff.FOCUS]
        offensive_bonus = 0
        defensive_bonus = 0
        if user_is_character:
            for ability in user.autoabilities:
                offensive_bonus += MAGIC_BONUSES.get(ability, 0)
        if target_is_character:
            for ability in target.autoabilities:
                defensive_bonus += MAGIC_DEF_BONUSES.get(ability, 0)
        if (action.damage_type == DamageType.MAGIC
                and Status.MENTAL_BREAK not in target.statuses):
            defensive_stat = max(target.stats[Stat.MAGIC_DEFENSE], 1)
        else:
            defensive_stat = 0
    if damage_type in (DamageType.STRENGTH, DamageType.SPECIAL_STRENGTH,
                       DamageType.SPECIAL_MAGIC):
        power = offensive_stat * offensive_stat * offensive_stat
        power = (power // 0x20) + 0x1e
    else:  # MAGIC
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
    damage = damage + (damage * offensive_bonus // 100)
    damage = damage - (damage * defensive_bonus // 100)
    if damage_type is DamageType.STRENGTH:
        if Status.PROTECT in target.statuses:
            damage = damage // 2
        if Status.BERSERK in user.statuses:
            damage = int(damage * 1.5)
        if Status.POWER_BREAK in user.statuses:
            damage = damage // 2
        if Status.DEFEND in target.statuses:
            damage = damage // 2
        if (user_is_character
                and target.armored
                and Autoability.PIERCING not in user.autoabilities
                and Status.ARMOR_BREAK not in target.statuses):
            damage = damage // 3
    elif damage_type is DamageType.MAGIC:
        if Status.SHELL in target.statuses:
            damage = damage // 2
        if Status.MAGIC_BREAK in user.statuses:
            damage = damage // 2
    if damage < 0 and Status.ZOMBIE in target.statuses:
        damage = damage * -1
    if action.drains:
        if Status.ZOMBIE in user.statuses:
            damage = damage * -1
        if Status.ZOMBIE in target.statuses:
            damage = damage * -1
    if Status.BOOST in target.statuses:
        damage = int(damage * 1.5)
    if Status.SHIELD in target.statuses:
        damage = damage // 4
    if action.timer:
        time_remaining = min(time_remaining, action.timer)
        damage += damage * time_remaining // (action.timer * 2)
    if user_is_character:
        if Autoability.BREAK_DAMAGE_LIMIT in user.autoabilities:
            damage_limit = 99999
        else:
            damage_limit = 9999
    else:
        # TODO
        # not all monster actions have a damage limit of 99999
        damage_limit = 99999
    damage = min(damage, damage_limit)
    if action.damages_mp:
        damage = min(damage, target.current_mp)
    return damage
