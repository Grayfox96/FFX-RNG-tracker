from copy import deepcopy
from dataclasses import dataclass
from itertools import count

from ..utils import add_bytes, open_cp1252, stringify
from .constants import (COUNTER_TARGET_TYPES, HIT_CHANCE_FORMULA_TABLE, Buff,
                        Character, DamageFormula, DamageType, Element,
                        HitChanceFormula, MonsterSlot, Status, TargetType)
from .file_functions import get_resource_path
from .statuses import NO_RNG_STATUSES, StatusApplication
from .text_characters import bytes_to_string


@dataclass
class Action:
    name: str
    description: str
    is_character_action: bool
    exclusive_user: Character | None
    can_use_in_combat: bool
    rank: int
    mp_cost: int
    od_cost: int
    target: TargetType | Character | MonsterSlot | None
    can_target_dead: bool
    long_range: bool
    hit_chance_formula: HitChanceFormula
    uses_hit_chance_table: bool
    accuracy: int
    misses_if_target_alive: bool
    affected_by_dark: bool
    damage_formula: DamageFormula
    damage_type: DamageType
    base_damage: int
    damages_hp: bool
    damages_mp: bool
    damages_ctb: bool
    heals: bool
    uses_weapon_properties: bool
    ignores_armored: bool
    never_break_damage_limit: bool
    always_break_damage_limit: bool
    n_of_hits: int
    elements: set[Element]
    can_crit: bool
    bonus_crit: int
    adds_equipment_crit: bool
    statuses: dict[Status, StatusApplication]
    status_flags: set[Status]
    removes_statuses: bool
    has_weak_delay: bool
    has_strong_delay: bool
    shatter_chance: int
    buffs: dict[Buff, int]
    drains: bool
    affected_by_reflect: bool
    affected_by_silence: bool
    steals_item: bool
    steals_gil: bool
    destroys_user: bool
    empties_od_bar: bool
    copied_by_copycat: bool
    overdrive_user: Character
    overdrive_index: int

    def __str__(self) -> str:
        return self.name

    @property
    def is_counter(self) -> bool:
        return self.target in COUNTER_TARGET_TYPES


@dataclass(frozen=True)
class YojimboAction:
    name: str
    compatibility_modifier: int
    needed_motivation: int | None = None

    def __str__(self) -> str:
        return self.name


def parse_actions_file(file_path: str) -> list[Action]:
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data = file_object.read()
    actions_data = [[int(b, 16) for b in line.split(',')]
                    for line in data.splitlines()]
    string_data = actions_data.pop()
    actions = []
    for action in actions_data:
        name = bytes_to_string(string_data, add_bytes(*action[0:2]))

        description = bytes_to_string(string_data, add_bytes(*action[8:10]))

        is_character_action = len(action) == 96

        if is_character_action and action[25] != 255:
            exclusive_user = tuple(Character)[action[25]]
        else:
            exclusive_user = None

        can_target_dead = bool(action[26] & 0b01000000)
        long_range = bool(action[26] & 0b10000000)

        # targetsAllowedApparently = action[27]

        # can_use_in_menu = bool(action[28] & 0x01)
        can_use_in_combat = bool(action[28] & 0x02)
        hit_chance_formula_index = (action[28] // 0x08) % 8
        hit_chance_formula = HIT_CHANCE_FORMULA_TABLE[hit_chance_formula_index]
        uses_hit_chance_table = bool((action[28] & 0x08)
                                     or hit_chance_formula_index == 6)
        affected_by_dark = bool(action[28] & 0x40)
        affected_by_reflect = bool(action[28] & 0x80)

        drains = bool(action[29] & 0x01)
        steals_item = bool(action[29] & 0x02)
        has_weak_delay = bool(action[29] & 0x20)
        has_strong_delay = bool(action[29] & 0x40)

        ignores_armored = bool(action[30] & 0x01)
        affected_by_silence = bool(action[30] & 0x02)
        uses_weapon_properties = bool(action[30] & 0x04)
        destroys_user = bool(action[30] & 0x40)
        misses_if_target_alive = bool(action[30] & 0x80)

        empties_od_bar = bool(action[31] & 0x02)
        copied_by_copycat = bool(action[31] & 0x10)

        if action[32] & 0b01:
            damage_type = DamageType.PHYSICAL
        elif action[32] & 0b10:
            damage_type = DamageType.MAGICAL
        else:
            damage_type = DamageType.OTHER
        can_crit = bool(action[32] & 0x04)
        adds_equipment_crit = bool(action[32] & 0x08)
        heals = bool(action[32] & 0x10)
        removes_statuses = bool(action[32] & 0x20)
        never_break_damage_limit = bool(action[32] & 0x40)
        always_break_damage_limit = bool(action[32] & 0x80)

        steals_gil = bool(action[33] & 0x01)

        damages_hp = bool(action[35] & 0x01)
        damages_mp = bool(action[35] & 0x02)
        damages_ctb = bool(action[35] & 0x04)

        rank = action[36]
        mp_cost = action[37]
        od_cost = action[38]
        bonus_crit = action[39]
        damage_formula = tuple(DamageFormula)[action[40]]
        accuracy = action[41]
        base_damage = action[42]
        n_of_hits = action[43]
        shatter_chance = action[44]

        elements: set[Element] = set()
        for i, element in enumerate(Element):
            if action[45] & (1 << i):
                elements.add(element)

        statuses: dict[Status, StatusApplication] = {}
        for i, status in enumerate(Status, 46):
            if i < 58:
                stacks = 254
            elif i > 70:
                break
            else:
                stacks = action[i + 13]
            chance = action[i]
            if chance > 0:
                statuses[status] = StatusApplication(status, chance, stacks)

        status_flags: set[Status] = set()
        status_flags_bytes = add_bytes(action[84], action[85], action[90])
        for i, status_flag in enumerate(NO_RNG_STATUSES):
            if i > 3:
                i += 1
            if i > 13:
                i += 1
            if status_flags_bytes & (1 << i):
                status_flags.add(status_flag)

        buff_stacks = action[89]
        buffs = {}
        for i, buff in enumerate(Buff):
            if action[86] & (1 << i):
                buffs[buff] = buff_stacks

        overdrive_info = action[88]
        if overdrive_info:
            overdrive_user = tuple(Character)[overdrive_info & 0b1111]
        else:
            overdrive_user = None
        overdrive_index = overdrive_info >> 4

        target = get_target(is_character_action, action[26], action[29],
                            overdrive_user, overdrive_index)

        action = Action(
            name=name,
            description=description,
            is_character_action=is_character_action,
            exclusive_user=exclusive_user,
            can_use_in_combat=can_use_in_combat,
            rank=rank,
            mp_cost=mp_cost,
            od_cost=od_cost,
            target=target,
            can_target_dead=can_target_dead,
            long_range=long_range,
            hit_chance_formula=hit_chance_formula,
            uses_hit_chance_table=uses_hit_chance_table,
            accuracy=accuracy,
            misses_if_target_alive=misses_if_target_alive,
            affected_by_dark=affected_by_dark,
            damage_formula=damage_formula,
            damage_type=damage_type,
            base_damage=base_damage,
            damages_hp=damages_hp,
            damages_mp=damages_mp,
            damages_ctb=damages_ctb,
            heals=heals,
            uses_weapon_properties=uses_weapon_properties,
            ignores_armored=ignores_armored,
            never_break_damage_limit=never_break_damage_limit,
            always_break_damage_limit=always_break_damage_limit,
            n_of_hits=n_of_hits,
            elements=elements,
            can_crit=can_crit,
            bonus_crit=bonus_crit,
            adds_equipment_crit=adds_equipment_crit,
            statuses=statuses,
            status_flags=status_flags,
            removes_statuses=removes_statuses,
            has_weak_delay=has_weak_delay,
            has_strong_delay=has_strong_delay,
            shatter_chance=shatter_chance,
            buffs=buffs,
            drains=drains,
            affected_by_reflect=affected_by_reflect,
            affected_by_silence=affected_by_silence,
            steals_item=steals_item,
            steals_gil=steals_gil,
            destroys_user=destroys_user,
            empties_od_bar=empties_od_bar,
            copied_by_copycat=copied_by_copycat,
            overdrive_user=overdrive_user,
            overdrive_index=overdrive_index,
        )
        actions.append(action)
    return actions


def get_target(is_character_action: bool,
               targeting_byte: int,
               random_targeting_byte: bool,
               overdrive_user: Character,
               overdrive_index: int,
               ) -> TargetType | None:
    has_target = bool(targeting_byte & 0b00000001)
    targets_enemies_by_default = bool(targeting_byte & 0b00000010)
    aoe = bool(targeting_byte & 0b00000100)
    targets_self = bool(targeting_byte & 0b00001000)
    # ??? = bool(targeting_byte & 0b00010000)
    can_switch_party = bool(targeting_byte & 0b00100000)
    random_targeting = bool(random_targeting_byte & 0x80)

    if overdrive_index == 1:
        return None
    if not has_target:
        return None
    if is_character_action:
        if can_switch_party:
            if aoe:
                target = TargetType.PARTY
            else:
                target = TargetType.SINGLE
        elif targets_enemies_by_default:
            if random_targeting:
                target = TargetType.RANDOM_MONSTER
            elif aoe:
                target = TargetType.MONSTERS_PARTY
            elif overdrive_user is Character.WAKKA:
                target = TargetType.RANDOM_MONSTER
            else:
                target = TargetType.SINGLE_MONSTER
        elif random_targeting:
            target = TargetType.RANDOM_CHARACTER
        elif targets_self:
            target = TargetType.SELF
        elif aoe:
            target = TargetType.CHARACTERS_PARTY
        elif overdrive_user is Character.RIKKU:
            target = TargetType.RANDOM_CHARACTER
        else:
            target = TargetType.SINGLE_CHARACTER
    elif random_targeting:
        target = TargetType.RANDOM_CHARACTER
    elif targets_enemies_by_default:
        if aoe:
            target = TargetType.CHARACTERS_PARTY
        elif targets_self:
            target = TargetType.CHARACTERS_PARTY
        else:
            target = TargetType.SINGLE_CHARACTER
    elif aoe:
        target = TargetType.MONSTERS_PARTY
    elif targets_self:
        target = TargetType.SELF
    else:
        target = TargetType.SINGLE_MONSTER
    return target


def get_character_actions() -> dict[str, Action]:
    actions_list = ITEM_BIN + COMMAND_BIN
    actions: dict[str, Action] = {}
    for index, action in enumerate(actions_list):
        action_id = stringify(action.name)

        if action.overdrive_user is Character.RIKKU:
            # some mixes share names with items
            if action_id in actions:
                action.name = f'Mix {action.name}'
                action_id = stringify(action.name)
        elif action.overdrive_user is Character.TIDUS:
            if 347 <= index <= 350:
                base_name = actions_list[index - 139].name
                action.name = f'{base_name} (Fail)'
                action_id = stringify(action.name)
            elif index == 386:
                base_name = actions_list[index - 175].name
                action.name = f'{base_name} (Last Hit)'
                action_id = stringify(action.name)
        elif action.overdrive_user is Character.AURON:
            if 378 <= index <= 381:
                base_name = actions_list[index - 166].name
                action.name = f'{base_name} (Fail)'
                action_id = stringify(action.name)
            if 382 <= index <= 385:
                base_name = actions_list[index - 170].name
                action.name = f'{base_name} (Immune)'
                action_id = stringify(action.name)
        elif action.overdrive_user is Character.WAKKA:
            # element/attack/status/auroch reels
            if 228 <= index <= 231:
                action.name = f'{action.name} (Unused)'
                action_id = stringify(action.name)
            # aoe shots that also have a single target counterpart
            elif index in (352, 354, 356, 358, 360, 362, 364):
                base_name = actions_list[index - 1].name
                action.name = f'{base_name} (AoE)'
                action_id = stringify(action.name)
        if action_id in actions:
            for i in count(2):
                new_name = f'{action_id}_{i}'
                if new_name not in actions:
                    action.name = f'{action.name} #{i}'
                    action_id = new_name
                    break
        actions[action_id] = action
    counter = deepcopy(actions['attack'])
    counter.target = TargetType.COUNTER
    counter.name = 'Counter'
    actions['counter'] = counter

    attacknocrit = deepcopy(actions['attack'])
    attacknocrit.name = 'Attack (No Crit)'
    attacknocrit.can_crit = False
    actions['attacknocrit'] = attacknocrit

    does_nothing = deepcopy(actions['switch'])
    does_nothing.name = 'Does Nothing'
    actions['does_nothing'] = does_nothing

    quick_hit_hd = actions.pop('quick_hit')
    quick_hit_hd.name = 'Quick Hit (HD)'
    actions['quick_hit_hd'] = quick_hit_hd

    quick_hit_ps2 = deepcopy(quick_hit_hd)
    quick_hit_ps2.name = 'Quick Hit (PS2)'
    quick_hit_ps2.rank = 1
    actions['quick_hit_ps2'] = quick_hit_ps2
    return actions


ITEM_BIN = parse_actions_file('data_files/ffx_item.csv')
COMMAND_BIN = parse_actions_file('data_files/ffx_command.csv')
ACTIONS = get_character_actions()
MONMAGIC1_BIN = parse_actions_file('data_files/ffx_monmagic1.csv')
MONMAGIC2_BIN = parse_actions_file('data_files/ffx_monmagic2.csv')

ACTIONS_FILES_BY_ID = {
    2: ITEM_BIN,
    3: COMMAND_BIN,
    4: MONMAGIC1_BIN,
    6: MONMAGIC2_BIN,
}

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

OD_TIMERS = {
    Character.TIDUS: 3000,
    Character.AURON: 4000,
    Character.WAKKA: 20000,
}
