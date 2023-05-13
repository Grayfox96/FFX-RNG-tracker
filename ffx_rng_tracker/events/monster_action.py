from dataclasses import dataclass

from ..data.actions import Action
from ..data.characters import CharacterState
from ..data.constants import (Buff, Character, DamageType, MonsterSlot, Stat,
                              Status, TargetType)
from ..data.monsters import MonsterState, get_monsters_dict
from ..data.statuses import NO_RNG_STATUSES
from .character_action import get_damage
from .main import Event


@dataclass
class MonsterAction(Event):
    monster: MonsterState
    action: Action

    def __post_init__(self) -> None:
        self.gamestate.process_start_of_turn(self.monster)
        self.targets = self._get_targets()
        self.hits = self._get_hits()
        self.statuses = self._get_statuses()
        self.removed_statuses = self._remove_statuses()
        self.damage_rngs, self.crits = self._get_damage_rngs()
        self.damages = self._get_damages()
        self.ctb = self._get_ctb()
        self.gamestate.process_end_of_turn(self.monster)

    def __str__(self) -> str:
        actions = []
        for i, target in enumerate(self.targets):
            hit = self.hits[i]
            damage = self.damages[i]
            damage_rng = self.damage_rngs[i]
            crit = self.crits[i]
            statuses = self.statuses[i]
            removed_statuses = self.removed_statuses[i]
            action = f'{target} ->'
            if hit:
                if self.action.does_damage:
                    action += f' [{damage_rng}/31]'
                    action += f' {damage}'
                    if crit:
                        action += ' (Crit)'
                else:
                    action += ' (No damage)'
                if statuses:
                    action += ' '
                    for status, applied in statuses.items():
                        if applied:
                            action += f'[{status}]'
                        else:
                            action += f'[{status} Fail]'
                if removed_statuses:
                    action += ' '
                    statuses = [f'[-{s}]' for s in removed_statuses]
                    action += ''.join(statuses)
            else:
                action += ' Miss'
            actions.append(action)
        string = (f'{self.monster} -> '
                  f'{self.action} [{self.ctb}]')
        if actions:
            string += ': ' + ', '.join(actions)
        return string

    def _get_hits(self) -> list[bool]:
        index = min(44 + self.monster.slot, 51)
        luck = max(self.monster.stats[Stat.LUCK], 1)
        aims = self.monster.buffs[Buff.AIM]
        hits = []
        for target in self.targets:
            if not self.action.can_miss:
                hits.append(True)
                continue
            hit_rng = self._advance_rng(index) % 101
            target_evasion = target.stats[Stat.EVASION]
            target_luck = max(target.stats[Stat.LUCK], 1)
            target_reflexes = target.buffs[Buff.REFLEX]
            base_hit_chance = self.action.accuracy - target_evasion
            if Status.DARK in self.monster.statuses:
                base_hit_chance = base_hit_chance * 0x66666667 // 0xffffffff
                base_hit_chance = base_hit_chance // 4
            hit_chance = (base_hit_chance
                          + luck
                          - target_luck
                          + ((aims - target_reflexes) * 10))
            hits.append(hit_chance > hit_rng)
        return hits

    def _get_damage_rngs(self) -> tuple[list[int], list[bool]]:
        index = min(28 + self.monster.slot, 35)
        luck = self.monster.stats[Stat.LUCK]
        luck += self.monster.buffs[Buff.LUCK] * 10
        damage_rngs = []
        crits = []
        for target, hit in zip(self.targets, self.hits):
            if not hit or not self.action.does_damage:
                damage_rngs.append(0)
                crits.append(False)
                continue
            damage_rngs.append(self._advance_rng(index) & 31)
            if not self.action.can_crit:
                crits.append(False)
                continue
            crit_roll = self._advance_rng(index) % 101
            target_luck = max(target.stats[Stat.LUCK], 1)
            target_luck -= target.buffs[Buff.JINX] * 10
            crit_chance = luck - target_luck
            crit_chance += self.action.bonus_crit
            crits.append(crit_roll < crit_chance)
        return damage_rngs, crits

    def _get_damages(self) -> list[int]:
        damages = []
        for target, hit, damage_rng, crit in zip(self.targets, self.hits,
                                                 self.damage_rngs, self.crits):
            if not hit or not self.action.does_damage:
                damages.append(0)
                continue
            damage = get_damage(
                self.monster, self.action, target, damage_rng, crit)
            damages.append(damage)
            if self.action.damages_mp:
                target.current_mp -= damage
                if self.action.drains:
                    self.monster.current_mp += damage
            elif self.action.damage_type is DamageType.CTB:
                target.ctb -= damage
            else:
                target.current_hp -= damage
                if self.action.drains:
                    self.monster.current_hp += damage
        return damages

    def _get_statuses(self) -> list[dict[Status, bool]]:
        index = min(60 + self.monster.slot, 67)
        statuses = []
        for target, hit in zip(self.targets, self.hits):
            if not hit:
                statuses.append({})
                continue
            statuses_applied = {}
            for status, status_application in self.action.statuses.items():
                if status in NO_RNG_STATUSES:
                    status_rng = 0
                else:
                    status_rng = self._advance_rng(index) % 101
                resistance = target.status_resistances.get(status, 0)
                if status_application.chance == 255:
                    applied = True
                elif resistance == 255:
                    applied = False
                elif status_application.chance == 254:
                    applied = True
                elif (status_application.chance - resistance) > status_rng:
                    applied = True
                else:
                    applied = False
                statuses_applied[status] = applied
                if not applied:
                    continue
                if status is Status.DELAY_WEAK:
                    target.ctb += target.base_ctb * 3 // 2
                    continue
                elif status is Status.DELAY_STRONG:
                    target.ctb += target.base_ctb * 3
                    continue
                elif status is Status.HASTE:
                    if target.statuses.get(Status.SLOW, 0) >= 255:
                        continue
                    target.statuses.pop(Status.SLOW, None)
                elif status is Status.SLOW:
                    if target.statuses.get(Status.HASTE, 0) >= 255:
                        continue
                    target.statuses.pop(Status.HASTE, None)
                target.statuses[status] = status_application.stacks
            if Status.PETRIFY in target.statuses:
                # TODO
                # check if "% 101" is correct
                shatter_rng = self._advance_rng(index) % 101
                if self.action.shatter_chance > shatter_rng:
                    target.statuses.pop(Status.PETRIFY)
                    target.statuses[Status.DEATH] = 254
                    statuses_applied[Status.DEATH] = True
                    target.statuses[Status.EJECT] = 254
                    statuses_applied[Status.EJECT] = True
            statuses.append(statuses_applied)
        return statuses

    def _remove_statuses(self) -> list[list[Status]]:
        statuses = []
        for target, hit in zip(self.targets, self.hits):
            if not hit:
                statuses.append([])
                continue
            statuses_removed = []
            for status in self.action.dispels:
                if status not in target.statuses:
                    continue
                if target.statuses[status] >= 255:
                    continue
                removed_status = target.statuses.pop(status)
                if removed_status is Status.DEATH:
                    target.ctb = target.base_ctb * 3
                statuses_removed.append(removed_status)
            statuses.append(statuses_removed)
        return statuses

    def _get_possible_targets(self) -> list[CharacterState]:
        targets = []
        active_party = sorted(
            self.gamestate.party, key=lambda c: tuple(Character).index(c))
        for character in active_party:
            state = self.gamestate.characters[character]
            if (state.dead
                    or Status.ESCAPE in state.statuses):
                continue
            targets.append(state)
        if not targets:
            targets.append(self.gamestate.characters[Character.UNKNOWN])
        return targets

    def _get_targets(self) -> list[CharacterState] | list[MonsterState]:
        possible_targets = self._get_possible_targets()
        target = self.action.target

        match target:
            case TargetType.SELF:
                possible_targets = [self.monster]
            case TargetType.SINGLE | TargetType.SINGLE_CHARACTER | TargetType.RANDOM_CHARACTER:
                pass
            case TargetType.SINGLE_MONSTER | TargetType.RANDOM_MONSTER:
                if self.gamestate.monster_party:
                    possible_targets = self.gamestate.monster_party
                else:
                    monsters = get_monsters_dict()
                    possible_targets = [MonsterState(monsters['dummy'])]
            case TargetType.HIGHEST_HP_CHARACTER:
                if len(possible_targets) > 1:
                    possible_targets.sort(
                        key=lambda c: c.current_hp, reverse=True)
                    possible_targets = [possible_targets[0]] * 2
            case TargetType.LOWEST_HP_CHARACTER:
                if len(possible_targets) > 1:
                    possible_targets.sort(key=lambda c: c.current_hp)
                    possible_targets = [possible_targets[0]] * 2
            case TargetType.ALL | TargetType.ALL_CHARACTERS:
                possible_targets.sort(
                    key=lambda c: tuple(Character).index(c.character))
                return possible_targets * self.action.hits
            case Character():
                if target in [c.character for c in possible_targets]:
                    possible_targets = [self.gamestate.characters[target]]
                else:
                    monsters = get_monsters_dict()
                    possible_targets = [MonsterState(monsters['dummy'])]
            case MonsterSlot():
                if len(self.gamestate.monster_party) > target:
                    possible_targets = [self.gamestate.monster_party[target]]
                else:
                    monsters = get_monsters_dict()
                    possible_targets = [MonsterState(monsters['dummy'])]
            case TargetType.LAST_ACTOR:
                possible_targets = [self.gamestate.last_actor]
            case _:
                return possible_targets * self.action.hits

        if len(possible_targets) == 1:
            return possible_targets * self.action.hits
        target_rng = self._advance_rng(4)
        target_index = target_rng % len(possible_targets)
        if self.action.hits == 1:
            return [possible_targets[target_index]]
        # TODO
        # set monster actions target to "Random character"
        # elif target in (TargetType.SINGLE, TargetType.SINGLE_CHARACTER):
        #     return [possible_targets[target_index]] * self.action.hits
        else:
            targets: list[CharacterState] = []
            for _ in range(self.action.hits):
                target_rng = self._advance_rng(5)
                target_index = target_rng % len(possible_targets)
                targets.append(possible_targets[target_index])
            targets.sort(key=lambda c: tuple(Character).index(c.character))
            return targets

    def _get_ctb(self) -> int:
        rank = self.action.rank
        ctb = self.monster.base_ctb * rank
        if Status.HASTE in self.monster.statuses:
            ctb = ctb // 2
        elif Status.SLOW in self.monster.statuses:
            ctb = ctb * 2
        self.monster.ctb += ctb
        return ctb
