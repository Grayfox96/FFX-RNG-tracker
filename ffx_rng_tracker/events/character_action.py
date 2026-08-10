from dataclasses import dataclass, field
from functools import cache
from typing import Literal

from ..data.actions import ACTIONS, OD_TIMERS, Action
from ..data.actor import Actor, CharacterActor, MonsterActor
from ..data.autoabilities import (DEFENSE_BONUSES, MAGIC_BONUSES,
                                  MAGIC_DEF_BONUSES, STRENGTH_BONUSES)
from ..data.constants import (ELEMENTAL_AFFINITY_MODIFIERS, HIT_CHANCE_TABLE,
                              Autoability, Buff, Character, DamageFormula,
                              DamageType, Element, ElementalAffinity,
                              HitChanceFormula, Stat, Status, SubMenu,
                              TargetType)
from ..data.statuses import NO_RNG_STATUSES, NUL_STATUSES
from .main import Event


@dataclass
class DamageInstance:
    damage: int = 0
    crit: bool = False
    damage_rng: int = 0
    pool: Literal['HP', 'MP', 'CTB'] = 'HP'

    def __str__(self) -> str:
        string = f'[{self.damage_rng}/31] {self.damage} {self.pool}'
        if self.crit:
            string += ' (Crit)'
        return string


@dataclass
class ActionResult:
    hit: bool = field(default=True, init=False)
    statuses: dict[Status, bool] = field(default_factory=dict, init=False)
    removed_statuses: list[Status] = field(default_factory=list, init=False)
    buffs: dict[Buff, int] = field(default_factory=dict, init=False)
    hp: DamageInstance = field(default_factory=DamageInstance, init=False)
    mp: DamageInstance = field(default_factory=DamageInstance, init=False)
    ctb: DamageInstance = field(default_factory=DamageInstance, init=False)

    def __post_init__(self) -> None:
        self.mp.pool = 'MP'
        self.ctb.pool = 'CTB'


@dataclass
class CharacterAction(Event):
    user: Actor
    action: Action
    target: list[Actor] | TargetType | Actor | None
    od_time_remaining: int = 0
    od_n_of_hits: int = 1

    def __post_init__(self) -> None:
        if not self.action.is_counter:
            self.gamestate.process_start_of_turn(self.user)
        self.mp_cost = self._get_mp_cost()
        self.targets = self._get_targets()
        self.results = [ActionResult() for _ in self.targets]
        self.reflected_targets: dict[int, Actor] = {}
        self._get_hits()
        self._get_damages()
        if not self.action.removes_statuses:
            self._get_statuses()
        else:
            self._remove_statuses()
        self._apply_damages()
        self._get_buffs()
        self._shatter_check()
        if self.action.is_counter:
            self.ctb = 0
        else:
            self.ctb = self._get_ctb()
            self.gamestate.process_end_of_turn(self.user, self.action)
        if self.action is ACTIONS['provoke']:
            for target in self.targets:
                target.provoker = self.user
        for target in self.targets:
            target.last_attacker = self.user
        self.user.last_targets = self.targets

    def __str__(self) -> str:
        actions = []
        for i, (target, result) in enumerate(zip(self.targets, self.results)):
            if not result.hit:
                actions.append(f'{target} -> Miss')
                continue
            action = ''
            if self.action.damage_formula is not DamageFormula.NO_DAMAGE:
                if self.action.damages_hp:
                    action += f' {result.hp}'
                if self.action.damages_mp:
                    action += f' {result.mp}'
                if self.action.damages_ctb:
                    action += f' {result.ctb}'
            if not action:
                action += ' (No damage)'
            if result.statuses:
                action += ' '
                for status, applied in result.statuses.items():
                    if applied:
                        action += f'[{status}]'
                    else:
                        action += f'[{status} Fail]'
            if result.removed_statuses:
                action += ' '
                statuses = [f'[-{s}]' for s in result.removed_statuses]
                action += ''.join(statuses)
            if result.buffs:
                action += ' '
                buffs = [f'[{b} {a}]' for b, a in result.buffs.items()]
                action += ' '.join(buffs)
            if not action:
                action = ' Does nothing'
            action = f'{target} ->{action}'
            if i in self.reflected_targets:
                action = f'{self.reflected_targets[i]} (reflected) -> {action}'
            actions.append(action)
        string = f'{self.user} -> {self.action} [{self.ctb}]: '
        if actions:
            string += f'\n{' ' * len(string)}'.join(actions)
        else:
            string += 'Does Nothing'
        return string

    @property
    def damage_rng_index(self) -> int:
        return min(20 + self.user.index, 27)

    @property
    def hit_rng_index(self) -> int:
        return min(36 + self.user.index, 43)

    @property
    def status_rng_index(self) -> int:
        return min(52 + self.user.index, 59)

    def _get_hits(self) -> None:
        index = self.hit_rng_index
        luck = max(self.user.stats[Stat.LUCK], 1)
        accuracy = self.user.stats[Stat.ACCURACY]
        aims = self.user.buffs[Buff.AIM]
        lucks = self.user.buffs[Buff.LUCK]

        elements = set(self.action.elements)
        if self.action.uses_weapon_properties:
            elements.update(self.user.weapon_elements)
        nul_statuses: set[Status] = set()
        for element in elements:
            if element in NUL_STATUSES:
                nul_statuses.add(NUL_STATUSES[element])

        for i, (target, result) in enumerate(zip(self.targets, self.results)):
            if (self.action.affected_by_reflect
                    and Status.REFLECT in target.statuses):
                self.reflected_targets[i] = target
                new_target = self._get_new_reflect_target(target)
                self.targets[i] = new_target
            if (self.action.misses_if_target_alive
                    and Status.DEATH not in target.statuses
                    and Status.ZOMBIE not in target.statuses):
                result.hit = False
                continue
            # if all the elements are covered by a nul status the
            # target is immune and decrease the amount of status stacks by 1
            if nul_statuses and nul_statuses.issubset(target.statuses):
                for nul_status in nul_statuses:
                    if target.statuses[nul_status] >= 254:
                        continue
                    target.statuses[nul_status] -= 1
                    result.removed_statuses.append(nul_status)
                    if target.statuses[nul_status] <= 0:
                        target.statuses.pop(nul_status)
                result.hit = False
                continue
            if (self.action.hit_chance_formula is HitChanceFormula.ALWAYS
                    or Status.SLEEP in target.statuses
                    or Status.PETRIFY in target.statuses):
                continue
            hit_rng = self._advance_rng(index) % 101
            target_evasion = target.stats[Stat.EVASION]
            target_luck = max(target.stats[Stat.LUCK], 1)
            target_reflexes = target.buffs[Buff.REFLEX]
            target_jinxes = target.buffs[Buff.JINX]
            if self.action.uses_hit_chance_table:
                match self.action.hit_chance_formula:
                    case HitChanceFormula.USE_ACCURACY:
                        hit_chance = accuracy
                    case HitChanceFormula.USE_ACCURACY_x_2_5:
                        hit_chance = accuracy * 5 // 2
                    case HitChanceFormula.USE_ACCURACY_x_1_5:
                        hit_chance = accuracy * 3 // 2
                    case HitChanceFormula.USE_ACCURACY_x_0_5:
                        hit_chance = accuracy // 2
                hit_chance = ((hit_chance * 2 * 0x66666667) // 0xffffffff) // 2
                hit_chance_index = hit_chance - target_evasion + 10
                hit_chance_index = min(max(0, hit_chance_index), 8)
                base_hit_chance = HIT_CHANCE_TABLE[hit_chance_index]
            elif (self.action.hit_chance_formula
                    is HitChanceFormula.USE_ACTION_ACCURACY):
                base_hit_chance = self.action.accuracy - target_evasion
            # TODO
            # base_hit_chance could be unbound if uses_hit_chance_table
            # is False and hit_chance_formula is not ALWAYS
            # or USE_ACTION_ACCURACY
            if (self.action.affected_by_dark
                    and Status.DARK in self.user.statuses):
                base_hit_chance = base_hit_chance * 0x66666667 // 0xffffffff
                base_hit_chance = base_hit_chance // 4
            hit_chance = (base_hit_chance
                          + luck
                          - target_luck
                          + lucks
                          + target_jinxes
                          + ((aims - target_reflexes) * 10))
            result.hit = hit_chance > hit_rng

    def _overdrives_rng_advances(self, n_of_targets: int) -> None:
        # overdrive index is 0 if the action is not an od
        # is 1 if the action is an overdrive menu (swordplay, bushido, etc)
        # is 2+ if its an actual overdrive
        if self.action.overdrive_index <= 1:
            return
        if not self.action.overdrive_user:
            return
        damage_rng_index = self.damage_rng_index
        status_rng_index = self.status_rng_index
        rng_rolls: dict[int, int] = {}
        match self.action.overdrive_user:
            case Character.TIDUS:
                if self.action.overdrive_index == 2:
                    # 1 damage roll and 1 crit roll before the timer
                    rng_rolls[damage_rng_index] = 2
                elif self.action.overdrive_index == 3:
                    # 6 damage rolls and 6 crit rolls before the timer
                    rng_rolls[damage_rng_index] = 2 * 6
                    # if more than 1 target, rng16 will be used in
                    # _get_targets() once for every "missed" hit,
                    # potentially to decide ties
                    if self.action.n_of_hits == 3 and n_of_targets == 1:
                        rng_rolls[16] = 3
                elif self.action.overdrive_index == 4:
                    # 1 damage roll and 1 crit roll per target before the timer
                    rng_rolls[damage_rng_index] = 2 * n_of_targets
                elif self.action.overdrive_index == 5:
                    # the post timer portion is a different action
                    # the success or fail actions both have 9 hits
                    if self.action.n_of_hits > 1:
                        # 9 damage rolls and 9 crit rolls before the timer
                        rng_rolls[damage_rng_index] = 9 * 2
            case Character.AURON:
                # 2 is shooting star
                if self.action.overdrive_index == 2:
                    # 1 damage roll and 1 crit roll before the timer
                    rng_rolls[damage_rng_index] = 2
                # 3 is dragon fang
                elif self.action.overdrive_index == 3:
                    # 1 damage roll and 1 crit roll per target
                    rng_rolls[damage_rng_index] = 2 * n_of_targets
                elif self.action.overdrive_index == 4:
                    # 1 damage roll and 1 crit roll before the timer
                    rng_rolls[damage_rng_index] = 2
                    # 4 status rolls before the timer
                    rng_rolls[status_rng_index] = 4
                elif self.action.overdrive_index == 5:
                    rng_rolls[damage_rng_index] = 2 * 2 * n_of_targets
            case Character.WAKKA:
                # 1 damage rolls per target before the timer
                rng_rolls[damage_rng_index] = n_of_targets
                # wakka ods roll rng19 once per hit no matter what
                # if more than 1 target the the rolls are used
                # to pick targets in _get_targets()
                if n_of_targets == 1:
                    # TODO
                    # should this be self.od_n_of_hits instead of 1?
                    rng_rolls[19] = 1
            case Character.LULU:
                if self.action.target is TargetType.RANDOM_MONSTER:
                    # rng5 will be rolled in _get_targets()
                    # its always rolled 16 times
                    # bio and death fury have no damage
                    if self.action.base_damage:
                        rng_rolls[damage_rng_index] = 16
                    # only bio and death fury have statuses
                    else:
                        rng_rolls[status_rng_index] = 16
                    # if more than 1 target, rng16 will be used in
                    # _get_targets() once for every "missed" hit,
                    # potentially to decide ties
                    if n_of_targets == 1:
                        rng_rolls[16] = min(max(0, 16 - self.od_n_of_hits), 15)
                # demi and ultima fury
                else:
                    # TODO
                    # do demi and ultima fury roll rng16?
                    rng_rolls[damage_rng_index] = 16 * n_of_targets
            case Character.RIKKU:
                # all mixes roll rng5 once unless they target
                # a random character (nulall, vitality, etc)
                if self.action.target is not TargetType.RANDOM_CHARACTER:
                    rng_rolls[5] = 1
            # yuna only has the grand summon menu
            # kimahri's ods work like normal actions
            case _:
                return
        for rng_index, times in rng_rolls.items():
            for _ in range(times):
                self._advance_rng(rng_index)

    def _get_crit(self, luck: int, target_luck: int) -> bool:
        if not self.action.can_crit:
            return False
        index = self.damage_rng_index
        crit_roll = self._advance_rng(index) % 101
        if Status.CRITICAL in self.user.statuses:
            return True
        crit_chance = luck - target_luck
        return crit_roll < crit_chance

    def _get_damages(self) -> None:
        if self.action.damage_formula is DamageFormula.NO_DAMAGE:
            return
        if (not self.action.damages_hp and not self.action.damages_mp
                and not self.action.damages_ctb):
            return
        index = self.damage_rng_index
        luck = self.user.stats[Stat.LUCK] + (self.user.buffs[Buff.LUCK] * 10)
        if self.action.adds_equipment_crit:
            luck += self.user.equipment_crit
        else:
            luck += self.action.bonus_crit

        for target, result in zip(self.targets, self.results):
            if not result.hit:
                continue
            target_luck = max(target.stats[Stat.LUCK], 1)
            target_luck -= target.buffs[Buff.JINX] * 10
            if self.action.damages_hp:
                result.hp.damage_rng = self._advance_rng(index) & 31
                result.hp.crit = self._get_crit(luck, target_luck)
                result.hp.damage = get_damage(
                    self.user, self.action, target, result.hp.damage_rng,
                    result.hp.crit, self.od_time_remaining, 'hp')
            if self.action.damages_mp:
                result.mp.damage_rng = self._advance_rng(index) & 31
                result.mp.crit = self._get_crit(luck, target_luck)
                result.mp.damage = get_damage(
                    self.user, self.action, target, result.mp.damage_rng,
                    result.mp.crit, self.od_time_remaining, 'mp')
                result.mp.damage = min(result.mp.damage, target.current_mp)
            if self.action.damages_ctb:
                result.ctb.damage_rng = self._advance_rng(index) & 31
                result.ctb.crit = self._get_crit(luck, target_luck)
                result.ctb.damage = get_damage(
                    self.user, self.action, target, result.ctb.damage_rng,
                    result.ctb.crit, self.od_time_remaining)

    def _apply_damages(self) -> None:
        for target, result in zip(self.targets, self.results):
            if result.hit is False or Status.PETRIFY in target.statuses:
                continue
            if self.action.damages_hp:
                target.current_hp -= result.hp.damage
                if self.action.drains:
                    self.user.current_hp += result.hp.damage
            if self.action.damages_mp:
                target.current_mp -= result.mp.damage
                if self.action.drains:
                    self.user.current_mp += result.mp.damage
            if self.action.damages_ctb:
                target.ctb += result.ctb.damage
                # if self.action.drains:
                #     self.user.ctb += result.ctb.damage

    def _get_statuses(self) -> None:
        index = self.status_rng_index
        for target, result in zip(self.targets, self.results):
            if not result.hit:
                continue
            status_applications = self.action.statuses.copy()
            if self.action.uses_weapon_properties:
                for application in self.user.weapon_statuses:
                    status = application.status
                    if status not in status_applications:
                        status_applications[status] = application
                    elif application.chance > status_applications[status].chance:
                        status_applications[status] = application
            for status, application in status_applications.items():
                if status in target.statuses:
                    continue
                if status is Status.HASTE and target.statuses.get(Status.SLOW, 0) >= 255:
                    continue
                elif status is Status.SLOW and target.statuses.get(Status.HASTE, 0) >= 255:
                    continue
                if status in NO_RNG_STATUSES:
                    status_rng = 0
                else:
                    status_rng = self._advance_rng(index) % 101
                resistance = target.status_resistances[status]
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
                result.statuses[status] = applied
                if not applied:
                    continue
                if status is Status.HASTE:
                    target.statuses.pop(Status.SLOW, None)
                elif status is Status.SLOW:
                    target.statuses.pop(Status.HASTE, None)
                target.statuses[status] = application.stacks
            for status in self.action.status_flags:
                if target.status_resistances[status] == 255:
                    continue
                result.statuses[status] = True
                target.statuses[status] = 254
            if Status.PETRIFY in target.statuses:
                petrify_stacks = target.statuses[Status.PETRIFY]
                target.statuses.clear()
                target.statuses[Status.PETRIFY] = petrify_stacks
            if Status.DEATH in target.statuses:
                target.current_hp = 0
            if self.action.has_weak_delay:
                target.ctb += target.base_ctb * 3 // 2
            if self.action.has_strong_delay:
                target.ctb += target.base_ctb * 3

    def _remove_statuses(self) -> None:
        for target, result in zip(self.targets, self.results):
            if not result.hit:
                continue
            for status in self.action.statuses:
                if status is Status.DEATH and Status.ZOMBIE in target.statuses:
                    if not target.immune_to_life:
                        result.statuses[Status.DEATH] = True
                        target.current_hp = 0
                    continue
                if (status not in target.statuses
                        or target.statuses[status] >= 255):
                    continue
                target.statuses.pop(status)
                if status is Status.DEATH:
                    target.ctb = target.base_ctb * 3
                    if self.action.is_counter:
                        target.ctb -= self.gamestate.ctb_since_last_action
                        # TODO
                        # adding this here because it is only a real issue
                        # when an action used as a counter revives
                        # a character with autoregen
                        # if auto-life and auto-phoenix are ever automated
                        # this should be removed
                        if Autoability.AUTO_REGEN in target.autoabilities:
                            target.current_hp += (int(self.gamestate.ctb_since_last_action
                                                      * (target.max_hp / 256))
                                                  + 100)
                result.removed_statuses.append(status)

    def _shatter_check(self) -> None:
        index = self.status_rng_index
        for target, result in zip(self.targets, self.results):
            if not result.hit:
                continue
            if Status.PETRIFY not in target.statuses:
                continue
            shatter_rng = self._advance_rng(index) % 101
            if (hasattr(target, 'monster')
                    or self.action.shatter_chance > shatter_rng):
                result.statuses[Status.DEATH] = True
                target.current_hp = 0
                result.statuses[Status.EJECT] = True
                target.statuses[Status.EJECT] = 254
            else:
                result.statuses[Status.EJECT] = False

    def _get_buffs(self) -> None:
        for target, result in zip(self.targets, self.results):
            if not result.hit or Status.PETRIFY in target.statuses:
                continue
            for buff, amount in self.action.buffs.items():
                amount += target.buffs[buff]
                target.set_buff(buff, amount)
                result.buffs[buff] = target.buffs[buff]

    def _get_possible_character_targets(self) -> list[CharacterActor]:
        targets: list[CharacterActor] = []
        for character in self.gamestate.party:
            actor = self.gamestate.characters[character]
            if (Status.DEATH in actor.statuses
                    and not self.action.can_target_dead):
                continue
            if Status.EJECT in actor.statuses:
                continue
            targets.append(actor)
        targets.sort(key=lambda c: c.index)
        return targets

    def _get_possible_monster_targets(self) -> list[MonsterActor]:
        targets = []
        for actor in self.gamestate.monster_party:
            if (Status.DEATH in actor.statuses
                    and not self.action.can_target_dead):
                continue
            targets.append(actor)
        return targets

    def _get_targets(self) -> list[Actor]:
        dummy_target = self.gamestate.characters[Character.UNKNOWN]
        if (self.action.overdrive_user is Character.WAKKA
                and self.action.base_damage == 10):
            # only applies to attack reels
            n_of_hits = min(max(0, self.od_n_of_hits), 12)
        elif self.action.overdrive_user is Character.LULU:
            n_of_hits = min(max(1, self.od_n_of_hits), 16)
        else:
            n_of_hits = self.action.n_of_hits
        match self.target:
            case list() if self.target:
                return self.target
            case TargetType.SELF | TargetType.COUNTER_SELF:
                possible_targets = [self.user]
            case TargetType.RANDOM_CHARACTER:
                possible_targets = self._get_possible_character_targets()
            case TargetType.RANDOM_MONSTER:
                possible_targets = self._get_possible_monster_targets()
            case TargetType.CHARACTERS_PARTY:
                targets = self._get_possible_character_targets()
                if not targets:
                    targets.append(dummy_target)
                self._overdrives_rng_advances(len(targets))
                return targets * n_of_hits
            case TargetType.MONSTERS_PARTY:
                targets = self._get_possible_monster_targets()
                if not targets:
                    targets.append(dummy_target)
                self._overdrives_rng_advances(len(targets))
                return targets * n_of_hits
            case TargetType.COUNTER:
                possible_targets = [self.gamestate.last_actor]
            case CharacterActor() | MonsterActor():
                possible_targets = [self.target]
            case None:
                return []
            case _:
                raise Exception(self.user, self.action, self.target)

        if not possible_targets:
            possible_targets.append(dummy_target)

        self._overdrives_rng_advances(len(possible_targets))

        if len(possible_targets) == 1:
            return possible_targets * max(1, n_of_hits)

        if self.action.overdrive_user is Character.WAKKA:
            rng_index = 19
        elif (self.action.overdrive_user is Character.RIKKU and
                self.action.target is TargetType.RANDOM_CHARACTER):
            rng_index = 4
        else:
            rng_index = 5

        targets: list[Actor] = []
        if ((self.action.overdrive_user is Character.TIDUS and n_of_hits == 3)
                or self.action.overdrive_user is Character.LULU):
            if self.action.overdrive_user is Character.TIDUS:
                targets_needed = 6
            elif self.action.overdrive_user is Character.LULU:
                targets_needed = 16

            for _ in range(targets_needed):
                target_rng = self._advance_rng(rng_index)
                target_index = target_rng % len(possible_targets)
                targets.append(possible_targets[target_index])

            while len(targets) > n_of_hits:
                targets_counts = [targets.count(t) for t in possible_targets]
                max_count = max(targets_counts)
                targets_at_max_count = [i for i, c in enumerate(targets_counts)
                                        if c == max_count]
                if len(targets_at_max_count) == 1:
                    index_to_remove = 0
                    self._advance_rng(16)
                else:
                    index_to_remove = (self._advance_rng(16)
                                       % len(targets_at_max_count))
                target_to_remove = targets_at_max_count[index_to_remove]
                targets.pop(targets.index(possible_targets[target_to_remove]))
        else:
            for _ in range(n_of_hits):
                target_rng = self._advance_rng(rng_index)
                target_index = target_rng % len(possible_targets)
                targets.append(possible_targets[target_index])

        targets.sort(key=lambda t: t.index)
        return targets

    def _get_new_reflect_target(self, target: Actor) -> Actor:
        if hasattr(target, 'monster'):
            possible_targets = self._get_possible_character_targets()
        else:
            possible_targets = self._get_possible_monster_targets()
        if len(possible_targets) == 0:
            return self.gamestate.characters[Character.UNKNOWN]
        elif len(possible_targets) == 1:
            return possible_targets[0]
        target_rng = self._advance_rng(6)
        target_index = target_rng % len(possible_targets)
        return possible_targets[target_index]

    def _get_ctb(self) -> int:
        if self.action.rank:
            rank = self.action.rank
        else:
            rank = 3
        ctb = self.user.base_ctb * rank
        if Status.HASTE in self.user.statuses:
            ctb = ctb // 2
        elif Status.SLOW in self.user.statuses:
            ctb = ctb * 2
        self.user.ctb += ctb
        return ctb

    def _get_mp_cost(self) -> int:
        if self.action.mp_cost == 0 or Status.MP_0 in self.user.statuses:
            mp_cost = 0
        elif Autoability.ONE_MP_COST in self.user.autoabilities:
            mp_cost = 1
        else:
            mp_cost = self.action.mp_cost
            if (self.action.submenu in (SubMenu.BLK_MAGIC, SubMenu.WHT_MAGIC)
                    and Autoability.MAGIC_BOOSTER in self.user.autoabilities):
                mp_cost *= 2
            if Autoability.HALF_MP_COST in self.user.autoabilities:
                mp_cost //= 2
        self.user.current_mp -= mp_cost
        return mp_cost


def get_element_mods(elemental_affinities: dict[Element, ElementalAffinity],
                     elements: set[Element],
                     ) -> list[float]:
    """returns a list of elemental modifiers"""
    if not elements:
        return [1.0]
    # if more than 1 element then only the stronger one applies
    # unless the target is weak to more than one
    # then apply all of those
    element_mods = [-1.0]
    for element in elements:
        affinity = elemental_affinities[element]
        if (element_mods[0] == 1.5
                and affinity is ElementalAffinity.WEAK):
            element_mods.append(ELEMENTAL_AFFINITY_MODIFIERS[affinity])
        else:
            element_mods[0] = max(
                element_mods[0],
                ELEMENTAL_AFFINITY_MODIFIERS[affinity])
    return element_mods


@cache
def _get_power(damage_formula: DamageFormula,
               base_damage: int,
               offensive_stat: int,
               ) -> int:
    match damage_formula:
        case (DamageFormula.STRENGTH | DamageFormula.PIERCING_STRENGTH
              | DamageFormula.SPECIAL_MAGIC):
            power = offensive_stat * offensive_stat * offensive_stat
            power = (power // 0x20) + 0x1e
        case DamageFormula.HEALING:
            power = (offensive_stat + base_damage) // 2 * base_damage
        case DamageFormula.MAGIC | DamageFormula.PIERCING_MAGIC:
            power = offensive_stat * offensive_stat
            power = (power * 0x2AAAAAAB) // 0xffffffff
            power = (power + base_damage) * base_damage // 4
        case _:
            raise NotImplementedError
    return power


@cache
def _get_mitigation(defensive_stat: int) -> int:
    mitigation_1 = defensive_stat * defensive_stat
    mitigation_1 = (mitigation_1 * 0x2E8BA2E9) // 0xffffffff
    mitigation_1 = mitigation_1 // 2
    mitigation = (defensive_stat * 0x33) - mitigation_1
    mitigation = (mitigation * 0x66666667) // 0xffffffff
    mitigation = 0x2da - (mitigation // 4)
    return mitigation


def get_damage(
        user: Actor,
        action: Action,
        target: Actor,
        damage_rng: int = 0,
        crit: bool = False,
        od_time_remaining: int = 0,
        pool: Literal['hp', 'mp'] = 'hp',
        ) -> int:
    if target.immune_to_damage:
        return 0
    if (target.immune_to_physical_damage
            and action.damage_type is DamageType.PHYSICAL):
        return 0
    if (target.immune_to_magical_damage
            and action.damage_type is DamageType.MAGICAL):
        return 0
    if action.uses_weapon_properties:
        base_damage = user.base_weapon_damage
    else:
        base_damage = action.base_damage

    match action.damage_formula:
        case DamageFormula.NO_DAMAGE:
            return 0
        case DamageFormula.FIXED:
            damage = base_damage * 50 * (damage_rng + 0xf0) // 256
        case DamageFormula.FIXED_NO_VARIANCE:
            damage = base_damage * 50
        case DamageFormula.PERCENTAGE_TOTAL:
            if target.immune_to_percentage_damage:
                damage = 0
            elif pool == 'hp':
                damage = target.max_hp * base_damage // 16
            else:
                damage = target.max_mp * base_damage // 16
        case DamageFormula.PERCENTAGE_CURRENT:
            if target.immune_to_percentage_damage:
                damage = 0
            elif pool == 'hp':
                damage = target.current_hp * base_damage // 16
            else:
                damage = target.current_mp * base_damage // 16
        case DamageFormula.HP:
            damage = user.max_hp * base_damage // 10
        case DamageFormula.GIL:
            # hijacking the od_time_remaining parameter, diving by 1000
            # because it normally represents milliseconds
            damage = (od_time_remaining // 1000) // 10
        case DamageFormula.CTB:
            damage = target.ctb * base_damage // 16
        case (DamageFormula.STRENGTH | DamageFormula.PIERCING_STRENGTH
              | DamageFormula.MAGIC | DamageFormula.PIERCING_MAGIC
              | DamageFormula.SPECIAL_MAGIC | DamageFormula.HEALING):
            if action.damage_formula in (DamageFormula.STRENGTH,
                                         DamageFormula.PIERCING_STRENGTH):
                offensive_stat = (user.stats[Stat.STRENGTH]
                                  + user.buffs[Buff.CHEER])
                if (action.damage_formula is DamageFormula.STRENGTH
                        and Status.ARMOR_BREAK not in target.statuses):
                    defensive_stat = max(target.stats[Stat.DEFENSE], 1)
                else:
                    defensive_stat = 0
                defensive_buffs = target.buffs[Buff.CHEER]
            elif action.damage_formula in (DamageFormula.MAGIC,
                                           DamageFormula.PIERCING_MAGIC,
                                           DamageFormula.SPECIAL_MAGIC):
                offensive_stat = (user.stats[Stat.MAGIC]
                                  + user.buffs[Buff.FOCUS])
                if (action.damage_formula is DamageFormula.MAGIC
                        and Status.MENTAL_BREAK not in target.statuses):
                    defensive_stat = max(target.stats[Stat.MAGIC_DEFENSE], 1)
                else:
                    defensive_stat = 0
                defensive_buffs = target.buffs[Buff.FOCUS]
            else:  # DamageFormula.HEALING
                offensive_stat = (user.stats[Stat.MAGIC]
                                  + user.buffs[Buff.FOCUS])
                defensive_stat = 0
                defensive_buffs = target.buffs[Buff.FOCUS]
            power = _get_power(
                action.damage_formula, base_damage, offensive_stat)
            mitigation = _get_mitigation(defensive_stat)
            damage_1 = power * mitigation
            damage_2 = (damage_1 * -1282606671) // 0xffffffff
            damage_3 = (damage_1 + damage_2) // 0x200 * (15 - defensive_buffs)
            damage_4 = (damage_3 * -2004318071) // 0xffffffff
            damage = (damage_3 + damage_4) // 0x8
            if action.damage_formula in (DamageFormula.STRENGTH,
                                         DamageFormula.PIERCING_STRENGTH,
                                         DamageFormula.SPECIAL_MAGIC):
                damage = damage * base_damage // 0x10
            damage = damage * (damage_rng + 0xf0) // 256
        case DamageFormula.DEAL_9999:
            damage = 9999 * action.base_damage
        case (DamageFormula.KILLS
              | DamageFormula.CELESTIAL_HIGH_HP
              | DamageFormula.CELESTIAL_HIGH_MP
              | DamageFormula.CELESTIAL_LOW_HP):
            return 0
        case (DamageFormula.PERCENTAGE_TOTAL_MP
              | DamageFormula.BASE_CTB
              | DamageFormula.PERCENTAGE_CURRENT_MP
              | DamageFormula.PIERCING_STRENGTH_NO_VARIANCE
              | DamageFormula.SPECIAL_MAGIC_NO_VARIANCE):
            raise NotImplementedError

    if crit:
        damage = damage * 2
    if Status.BOOST in target.statuses:
        damage = int(damage * 1.5)
    if Status.SHIELD in target.statuses:
        damage = damage // 4

    elements = set(action.elements)
    if action.uses_weapon_properties:
        elements.update(user.weapon_elements)
    for element_mod in get_element_mods(target.elemental_affinities, elements):
        damage = int(damage * element_mod)

    if action.damage_type is DamageType.PHYSICAL:
        if Status.PROTECT in target.statuses:
            damage = damage // 2
        if Status.BERSERK in user.statuses:
            damage = int(damage * 1.5)
        if Status.POWER_BREAK in user.statuses:
            damage = damage // 2
        if Status.DEFEND in target.statuses:
            damage = damage // 2
    if action.damage_type is DamageType.MAGICAL:
        if Autoability.MAGIC_BOOSTER in user.autoabilities:
            damage = int(damage * 1.5)
        if Status.SHELL in target.statuses:
            damage = damage // 2
        if Status.MAGIC_BREAK in user.statuses:
            damage = damage // 2

    if Autoability.ALCHEMY in user.autoabilities and action.affected_by_alchemy:
        damage *= 2

    offensive_bonus = 0
    defensive_bonus = 0
    if action.damage_type is DamageType.PHYSICAL:
        for ability in user.autoabilities:
            offensive_bonus += STRENGTH_BONUSES.get(ability, 0)
        for ability in target.autoabilities:
            defensive_bonus += DEFENSE_BONUSES.get(ability, 0)
    elif action.damage_type is DamageType.MAGICAL:
        for ability in user.autoabilities:
            offensive_bonus += MAGIC_BONUSES.get(ability, 0)
        for ability in target.autoabilities:
            defensive_bonus += MAGIC_DEF_BONUSES.get(ability, 0)
    damage = damage + (damage * offensive_bonus // 100)
    damage = damage - (damage * defensive_bonus // 100)

    if (target.armored
            and not action.ignores_armored
            and Autoability.PIERCING not in user.autoabilities
            and Status.ARMOR_BREAK not in target.statuses):
        damage = damage // 3
    if action.drains:
        if Status.ZOMBIE in user.statuses:
            damage = damage * -1
        if Status.ZOMBIE in target.statuses:
            damage = damage * -1
    if timer := OD_TIMERS.get(action.overdrive_user):
        # TODO
        # od time remaining is not every value in this range [0, timer]
        # instead is given by this formula
        # timer - (frames / fps)
        # where fps is 30, frames is frames since start of od
        # od time remaining can only be one of these 3
        # x.y666666
        # x.y333333
        # x.y0
        # where x and y are the integer digit and the 1st decimal digit
        # from the visual timer (the last digit is actually random)
        od_time_remaining = min(od_time_remaining, timer)
        damage += damage * od_time_remaining // (timer * 2)
    if action.never_break_damage_limit:
        damage_limit = 9999
    elif action.always_break_damage_limit:
        damage_limit = 99999
    elif Autoability.BREAK_DAMAGE_LIMIT in user.autoabilities:
        damage_limit = 99999
    else:
        damage_limit = 9999
    damage = min(damage, damage_limit)
    if action.heals and Status.ZOMBIE not in target.statuses:
        damage = damage * -1
    if Status.DAMAGE_9999 in user.statuses:
        if 0 <= damage <= 9999:
            damage = 9999
        elif -9999 <= damage <= -1:
            damage = -9999
    return damage
