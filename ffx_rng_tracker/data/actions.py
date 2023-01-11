import json
from dataclasses import dataclass, field

from ..utils import open_cp1252
from .constants import (Buff, Character, DamageType, Element, MonsterSlot,
                        Status, TargetType)
from .file_functions import get_resource_path
from .statuses import StatusApplication


@dataclass(frozen=True)
class Action:
    name: str
    target: TargetType | Character | MonsterSlot = TargetType.SINGLE
    can_miss: bool = True
    accuracy: int = 90
    does_damage: bool = True
    hits: int = 1
    uses_weapon: bool = False
    can_crit: bool = True
    bonus_crit: int = 0
    damage_type: DamageType = DamageType.STRENGTH
    damages_mp: bool = False
    base_damage: int = 0
    element: Element | None = None
    statuses: dict[Status, StatusApplication] = field(default_factory=dict)
    buffs: dict[Buff, int] = field(default_factory=dict)
    dispels: set[Status] = field(default_factory=set)
    shatter_chance: int = 10
    drains: bool = False
    timer: int = 0
    rank: int = 3

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class YojimboAction:
    name: str
    compatibility_modifier: int
    needed_motivation: int | None = None

    def __str__(self) -> str:
        return self.name


def _get_action(action: dict[str, str | dict[str, int]]) -> Action:
    if action.get('target') is not None:
        try:
            target = TargetType(action['target'])
        except ValueError:
            try:
                target = Character(action['target'])
            except ValueError:
                target = MonsterSlot(action['target'])
        action['target'] = target

    if action.get('damage_type') is not None:
        action['damage_type'] = DamageType(action['damage_type'])

    if action.get('element') is not None:
        action['element'] = Element(action['element'])

    if action.get('statuses') is not None:
        statuses: dict[str, tuple[int, int]] = action['statuses'].copy()
        action['statuses'].clear()
        for status, (chance, stacks) in statuses.items():
            status = Status(status)
            action['statuses'][status] = StatusApplication(
                status, chance, stacks)

    if action.get('buffs') is not None:
        buffs: dict[str, int] = action['buffs'].copy()
        action['buffs'].clear()
        for buff, amount in buffs.items():
            buff = Buff(buff)
            action['buffs'][buff] = amount

    if action.get('dispels') is not None:
        action['dispels'] = {Status(s) for s in action['dispels']}

    return Action(**action)


def _get_actions(file_path: str) -> dict[str, Action]:
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data: dict[str, dict] = json.load(file_object)
    actions = {}
    for name, action in data.items():
        if name.startswith('#'):
            continue
        actions[name] = _get_action(action)
    return actions


def _get_monster_actions(file_path: str) -> dict[str, dict[str, Action]]:
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data: dict[str, dict[str, dict]] = json.load(file_object)
    monster_actions = {}
    for monster_name, _actions in data.items():
        actions = {}
        for name, action in _actions.items():
            if name.startswith('#'):
                continue
            actions[name] = _get_action(action)
        monster_actions[monster_name] = actions
    return monster_actions


ACTIONS = _get_actions('data/actions.json')
MONSTER_ACTIONS = _get_monster_actions('data/monster_actions.json')

YOJIMBO_ACTIONS = {
    'daigoro': YojimboAction('Daigoro', -1, 0),
    'kozuka': YojimboAction('Kozuka', 0, 32),
    'wakizashi_st': YojimboAction('Wakizashi ST', 1, 48),
    'wakizashi_mt': YojimboAction('Wakizashi MT', 3, 63),
    'zanmato': YojimboAction('Zanmato', 4, 80),
    'dismiss': YojimboAction('Dismiss', 0),
    'first_turn_dismiss': YojimboAction('First turn Dismiss', -3),
    # 'death': YojimboAction('Death', -10),
    'autodismiss': YojimboAction('Autodismiss', -20),
}
