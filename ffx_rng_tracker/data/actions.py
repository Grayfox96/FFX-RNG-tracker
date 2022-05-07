import csv
from dataclasses import dataclass

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
    multitarget: bool
    random_targeting: bool
    hits: int
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
        file_reader = csv.reader(file_object, delimiter=',')
        # skips first line
        next(file_reader)
        actions = {}
        for line in file_reader:
            if line[0].startswith('#'):
                continue
            name = line[0].lower().replace(' ', '_')
            does_damage = line[5] == 'true'
            if does_damage:
                base_damage = int(line[10])
            else:
                base_damage = None
            try:
                damage_type = DamageType(line[9])
            except ValueError:
                damage_type = None
            try:
                element = Element(line[11])
            except ValueError:
                element = None
            actions[name] = Action(
                name=line[0],
                has_target=line[1] == 'true',
                can_miss=line[4] == 'true',
                does_damage=does_damage,
                can_crit=line[7] == 'true',
                uses_bonus_crit=line[8] == 'true',
                damage_type=damage_type,
                base_damage=base_damage,
                element=element,
                multitarget=line[2] == 'true',
                random_targeting=line[3] == 'true',
                hits=int(line[6]),
                rank=int(line[14]),
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
