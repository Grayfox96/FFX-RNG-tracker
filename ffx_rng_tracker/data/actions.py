import json
from dataclasses import dataclass

from .constants import DamageType, Element, Status
from .file_functions import get_resource_path


@dataclass(frozen=True)
class Action:
    name: str
    has_target: bool
    multitarget: bool
    random_targeting: bool
    can_miss: bool
    accuracy: int
    does_damage: bool
    hits: int
    can_crit: bool
    uses_bonus_crit: bool
    damage_type: DamageType
    base_damage: int
    element: Element
    statuses: dict[Status, int]
    rank: int

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class YojimboAction:
    name: str
    compatibility_modifier: int
    needed_motivation: int | None = None

    def __str__(self) -> str:
        return self.name


def _get_actions(file_path: str) -> dict[str, Action]:
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        data: dict[str, dict] = json.load(file_object)
    actions = {}
    for name, action in data.items():
        if name.startswith('#'):
            continue

        damage_type = action.get('damage type')
        if damage_type is not None:
            damage_type = DamageType(action['damage type'])

        element = action.get('element')
        if element is not None:
            element = Element(action['element'])

        statuses = {Status(s): v
                    for s, v in action.get('statuses', {}).items()}

        actions[name] = Action(
            name=action['name'],
            has_target=action.get('has target', True),
            multitarget=action.get('multitarget', False),
            random_targeting=action.get('random targeting', False),
            can_miss=action.get('can miss', True),
            accuracy=action.get('accuracy', 90),
            does_damage=action.get('does damage', True),
            hits=action.get('hits', 1),
            can_crit=action.get('can crit', True),
            uses_bonus_crit=action.get('uses bonus crit', True),
            damage_type=damage_type,
            base_damage=action.get('base damage', 16),
            element=element,
            statuses=statuses,
            rank=action.get('rank', 3),
        )
    return actions


ACTIONS = _get_actions('data/actions.json')

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
