from dataclasses import dataclass

from ..data.actor import Actor
from ..data.constants import Character, MonsterSlot, Stat, Status, TargetType
from .character_action import CharacterAction


@dataclass
class MonsterAction(CharacterAction):

    def _overdrives_rng_advances(self) -> None:
        return

    @property
    def damage_rng_index(self) -> int:
        return min(28 + self.user.index, 35)

    @property
    def hit_rng_index(self) -> int:
        return min(44 + self.user.index, 51)

    @property
    def status_rng_index(self) -> int:
        return min(60 + self.user.index, 67)

    def _get_targets(self) -> list[Actor]:
        dummy_target = self.gamestate.characters[Character.UNKNOWN]
        if self.target:
            target = self.target
        else:
            target = self.action.target
        match target:
            case TargetType.SELF | TargetType.COUNTER_SELF:
                possible_targets = [self.user]
            case TargetType.RANDOM_CHARACTER | TargetType.COUNTER_RANDOM_CHARACTER:
                possible_targets = self._get_possible_character_targets()
            case TargetType.HIGHEST_HP_CHARACTER:
                possible_targets = self._get_possible_character_targets()
                if len(possible_targets) > 1:
                    self._advance_rng(4)
                    possible_targets.sort(key=lambda c: c.current_hp)
                    possible_targets = [possible_targets[-1]]
            case TargetType.HIGHEST_STR_CHARACTER:
                possible_targets = self._get_possible_character_targets()
                if len(possible_targets) > 1:
                    self._advance_rng(4)
                    possible_targets.sort(key=lambda c: c.stats[Stat.STRENGTH])
                    possible_targets = [possible_targets[-1]]
            case TargetType.LOWEST_HP_CHARACTER:
                possible_targets = self._get_possible_character_targets()
                if len(possible_targets) > 1:
                    self._advance_rng(4)
                    possible_targets.sort(key=lambda c: c.current_hp)
                    possible_targets = [possible_targets[0]]
            case TargetType.HIGHEST_MP_CHARACTER:
                possible_targets = self._get_possible_character_targets()
                if len(possible_targets) > 1:
                    self._advance_rng(4)
                    possible_targets.sort(key=lambda c: c.current_mp)
                    possible_targets = [possible_targets[-1]]
            case TargetType.LOWEST_MAG_DEF_CHARACTER:
                possible_targets = self._get_possible_character_targets()
                if len(possible_targets) > 1:
                    self._advance_rng(4)
                    possible_targets.sort(
                        key=lambda c: c.stats[Stat.MAGIC_DEFENSE])
                    possible_targets = [possible_targets[0]]
            case TargetType.RANDOM_CHARACTER_REFLECT:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.REFLECT in c.statuses]
            case TargetType.RANDOM_CHARACTER_ZOMBIE:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.ZOMBIE in c.statuses]
            case TargetType.RANDOM_CHARACTER_PETRIFY:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.PETRIFY in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_PETRIFY:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.PETRIFY not in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_DOOM:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.DOOM not in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_BERSERK:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.BERSERK not in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_CONFUSE:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.CONFUSE not in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_CURSE:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.CURSE not in c.statuses]
            case TargetType.RANDOM_CHARACTER_NOT_POISON:
                possible_targets = [c for c
                                    in self._get_possible_character_targets()
                                    if Status.POISON not in c.statuses]
            case TargetType.CHARACTERS_PARTY | TargetType.COUNTER_CHARACTERS_PARTY:
                targets = self._get_possible_character_targets()
                if not targets:
                    targets.append(dummy_target)
                return targets * self.action.n_of_hits
            case TargetType.RANDOM_MONSTER:
                possible_targets = self._get_possible_monster_targets()
            case TargetType.RANDOM_MONSTER_NOT_SHELL:
                possible_targets = [m for m
                                    in self._get_possible_monster_targets()
                                    if Status.SHELL not in m.statuses]
            case TargetType.RANDOM_MONSTER_NOT_PROTECT:
                possible_targets = [m for m
                                    in self._get_possible_monster_targets()
                                    if Status.PROTECT not in m.statuses]
            case TargetType.RANDOM_MONSTER_NOT_REFLECT:
                possible_targets = [m for m
                                    in self._get_possible_monster_targets()
                                    if Status.REFLECT not in m.statuses]
            case TargetType.MONSTERS_PARTY:
                targets = self._get_possible_monster_targets()
                if not targets:
                    targets.append(dummy_target)
                return targets * self.action.n_of_hits
            case TargetType.ALL | TargetType.COUNTER_ALL:
                targets = (self._get_possible_character_targets()
                           + self._get_possible_monster_targets())
                if not targets:
                    targets.append(dummy_target)
                return targets * self.action.n_of_hits
            case TargetType.COUNTER:
                possible_targets = [self.gamestate.last_actor]
            case TargetType.PROVOKER:
                if self.user.provoker is not None:
                    return [self.user.provoker]
                possible_targets = []
            case TargetType.LAST_ATTACKER:
                if self.user.last_attacker is not None:
                    return [self.user.last_attacker]
                possible_targets = []
            case TargetType.LAST_TARGET | TargetType.COUNTER_LAST_TARGET:
                if self.user.last_target:
                    return [self.user.last_target]
                possible_targets = self._get_possible_character_targets()
            case Character() as character:
                possible_targets = self._get_possible_character_targets()
                if character in [c.character for c in possible_targets]:
                    possible_targets = [self.gamestate.characters[character]]
                else:
                    possible_targets = []
            case MonsterSlot() as slot:
                if len(self.gamestate.monster_party) > slot:
                    possible_targets = [self.gamestate.monster_party[slot]]
                else:
                    possible_targets = []
            case None:
                return []
            case _:
                raise Exception(self.user, self.action, self.target)

        if not possible_targets:
            possible_targets.append(dummy_target)
        if len(possible_targets) == 1:
            return possible_targets * max(1, self.action.n_of_hits)

        target_rng = self._advance_rng(4)
        target_index = target_rng % len(possible_targets)
        if self.action.n_of_hits == 1:
            return [possible_targets[target_index]]
        targets: list[Actor] = []
        for _ in range(self.action.n_of_hits):
            target_rng = self._advance_rng(5)
            target_index = target_rng % len(possible_targets)
            targets.append(possible_targets[target_index])
        targets.sort(key=lambda t: t.index)
        return targets
