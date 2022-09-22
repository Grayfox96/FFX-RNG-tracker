from dataclasses import dataclass, field

from ..data.actions import Action
from ..data.characters import CharacterState
from ..data.constants import (ICV_BASE, NO_RNG_STATUSES, Character,
                              MonsterSlot, Stat, Status, TargetType)
from ..data.monsters import MONSTERS, MonsterState
from .character_action import get_damage
from .main import Event


@dataclass
class MonsterAction(Event):
    monster: MonsterState
    action: Action
    targets: list[CharacterState] | list[MonsterState] = field(
        init=False, repr=False)
    hits: list[bool] = field(init=False, repr=False)
    statuses: list[dict[Status, int]] = field(init=False, repr=False)
    damages: list[int] = field(init=False, repr=False)
    damage_rngs: list[int] = field(init=False, repr=False)
    crits: list[bool] = field(init=False, repr=False)
    ctb: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.targets = self._get_targets()
        self.hits = self._get_hits()
        self.statuses = self._get_statuses()
        self.damage_rngs, self.crits = self._get_damage_rngs()
        self.damages = self._get_damages()
        self.ctb = self._get_ctb()

    def __str__(self) -> str:
        actions = []
        for i, target in enumerate(self.targets):
            hit = self.hits[i]
            damage = self.damages[i]
            damage_rng = self.damage_rngs[i]
            crit = self.crits[i]
            statuses = self.statuses[i]
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
                    action += ''
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
        # TODO
        aims = 0
        hits = []
        for target in self.targets:
            if not self.action.can_miss:
                hits.append(True)
                continue
            hit_rng = self._advance_rng(index) % 101
            target_evasion = target.stats[Stat.EVASION]
            target_luck = max(target.stats[Stat.LUCK], 1)
            # TODO
            target_reflexes = 0
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

    def _get_damage_rngs(self) -> list[int]:
        index = min(28 + self.monster.slot, 35)
        luck = self.monster.stats[Stat.LUCK]
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
            statuses_applied = {}
            for status, chance in self.action.statuses.items():
                if status in (Status.HASTE, Status.SLOW):
                    self._advance_rng(min(28 + self.monster.slot, 35))
                if status in NO_RNG_STATUSES:
                    status_rng = 0
                else:
                    status_rng = self._advance_rng(index) % 101
                resistance = target.status_resistances[status]
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
                statuses_applied[status] = applied
                if applied:
                    target.statuses.add(status)
                    if status is Status.PETRIFY:
                        # advance rng once more for shatter
                        # TODO
                        # add a shatter_chance property to action
                        self._advance_rng(index)
            statuses.append(statuses_applied)
        return statuses

    def _get_possible_targets(self) -> list[CharacterState]:
        targets = []
        for character in self.gamestate.party[:3]:
            state = self.gamestate.characters[character]
            if (Status.EJECT in state.statuses
                    or Status.DEATH in state.statuses):
                continue
            targets.append(state)
        if not targets:
            targets = [MonsterState(MONSTERS['dummy'])]
        return targets

    def _get_targets(self) -> list[CharacterState]:
        possible_targets = self._get_possible_targets()
        target = self.action.target

        match target:
            case TargetType.SELF:
                return [self.monster]
            case TargetType.SINGLE | TargetType.SINGLE_CHARACTER:
                pass
            case TargetType.ALL | TargetType.ALL_CHARACTERS:
                possible_targets.sort(
                    key=lambda c: tuple(Character).index(c.character))
                return possible_targets * self.action.hits
            case Character() if target in [c.character for c in possible_targets]:
                return [self.gamestate.characters[self.action.target]]
            case MonsterSlot() if len(self.gamestate.monster_party) >= target:
                return [self.gamestate.monster_party[self.action.target]]
            case TargetType.LAST_CHARACTER:
                return [self.gamestate.last_character]
            case _:
                return [MonsterState(MONSTERS['dummy'])]

        targets: list[CharacterState] = []
        if len(possible_targets) == 1:
            return possible_targets * self.action.hits
        target_rng = self._advance_rng(4)
        if self.action.hits == 1:
            target_index = target_rng % len(possible_targets)
            targets.append(possible_targets[target_index])
        elif self.action.hits > 1:
            for _ in range(self.action.hits):
                if len(possible_targets) == 1:
                    targets.append(possible_targets[0])
                    continue
                target_rng = self._advance_rng(5)
                target_index = target_rng % len(possible_targets)
                targets.append(possible_targets[target_index])
            targets.sort(key=lambda c: tuple(Character).index(c.character))
            return targets

        return targets

    def _get_ctb(self) -> int:
        rank = self.action.rank
        ctb_base = ICV_BASE[self.monster.stats[Stat.AGILITY]]
        return ctb_base * rank
