import csv
from dataclasses import dataclass
from typing import Dict, Optional

from .constants import DamageType, Element
from .file_functions import get_resource_path


@dataclass(frozen=True)
class Action:
    name: str
    has_target: bool
    can_miss: bool
    does_damage: bool
    can_crit: bool
    uses_bonus_crit: bool
    damage_type: DamageType
    base_damage: int
    element: Element

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class YojimboAction:
    name: str
    compatibility_modifier: int
    needed_motivation: Optional[int] = None

    def __str__(self) -> str:
        return self.name


def _get_actions(file_path: str) -> Dict[str, Action]:
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        file_reader = csv.reader(file_object, delimiter=',')
        # skips first line
        next(file_reader)
        actions = {}
        for line in file_reader:
            if line[0].startswith('#'):
                continue
            name = line[0].lower().replace(' ', '_')
            does_damage = line[3] == 'true'
            if does_damage:
                base_damage = int(line[7])
            else:
                base_damage = None
            try:
                damage_type = DamageType(line[6])
            except ValueError:
                damage_type = None
            try:
                element = Element(line[8])
            except ValueError:
                element = None
            actions[name] = Action(
                name=line[0],
                has_target=line[1] == 'true',
                can_miss=line[2] == 'true',
                does_damage=does_damage,
                can_crit=line[4] == 'true',
                uses_bonus_crit=line[5] == 'true',
                damage_type=damage_type,
                base_damage=base_damage,
                element=element,
            )
    return actions


ACTIONS = _get_actions('data/actions.csv')

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
