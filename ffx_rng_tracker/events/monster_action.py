from dataclasses import dataclass, field

from ..data.actions import Action
from ..data.characters import CharacterState
from ..data.constants import (NO_RNG_STATUSES, Character, DamageType,
                              MonsterSlot, Stat, Status, TargetType)
from ..data.monsters import MonsterState
from .character_action import get_damage
from .main import Event


@dataclass
class MonsterAction(Event):
    monster: MonsterState
    action: Action
    targets: list[CharacterState] | list[MonsterState] = field(
        init=False, repr=False)
    hits: list[bool] = field(init=False, repr=False)
    statuses: list[dict[Status, bool]] = field(init=False, repr=False)
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
        self.gamestate.normalize_ctbs()

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

    def _get_damage_rngs(self) -> tuple[list[int], list[bool]]:
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
            match self.action.damage_type:
                case DamageType.MAGIC_MP | DamageType.ITEM_MP | DamageType.PERCENTAGE_TOTAL_MP:
                    target.current_mp -= damage
                    if self.action.drains:
                        self.monster.current_mp += damage
                case DamageType.CTB:
                    target.ctb -= damage
                case _:
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
            for status, chance in self.action.statuses.items():
                if status in NO_RNG_STATUSES:
                    status_rng = 0
                else:
                    status_rng = self._advance_rng(index) % 101
                resistance = target.status_resistances.get(status, 0)
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
            if Status.PETRIFY in target.statuses:
                # TODO
                # check if "% 101" is correct
                shatter_rng = self._advance_rng(index) % 101
                if self.action.shatter_chance > shatter_rng:
                    target.statuses.add(Status.DEATH)
                    target.statuses.add(Status.EJECT)
            statuses.append(statuses_applied)
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
                possible_targets = self.gamestate.monster_party
            case TargetType.HIGHEST_HP_CHARACTER:
                if len(possible_targets) > 1:
                    possible_targets.sort(key=lambda c: c.current_hp, reverse=True)
                    possible_targets = [possible_targets[0]] * 2
            case TargetType.LOWEST_HP_CHARACTER:
                if len(possible_targets) > 1:
                    possible_targets.sort(key=lambda c: c.current_hp)
                    possible_targets = [possible_targets[0]] * 2
            case TargetType.ALL | TargetType.ALL_CHARACTERS:
                possible_targets.sort(
                    key=lambda c: tuple(Character).index(c.character))
                return possible_targets * self.action.hits
            case Character() if target in [c.character for c in possible_targets]:
                possible_targets = [self.gamestate.characters[target]]
            case MonsterSlot() if len(self.gamestate.monster_party) > target:
                possible_targets = [self.gamestate.monster_party[target]]
            case TargetType.LAST_CHARACTER:
                possible_targets = [self.gamestate.last_character]
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
