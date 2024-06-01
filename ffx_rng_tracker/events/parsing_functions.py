from enum import StrEnum
from typing import Protocol

from ..data.actions import ACTIONS, YOJIMBO_ACTIONS
from ..data.actor import Actor, MonsterActor
from ..data.characters import s_lv_to_total_ap
from ..data.constants import (SHORT_STATS_NAMES, Autoability, Character,
                              Element, ElementalAffinity, EquipmentType, Item,
                              KillType, MonsterSlot, Stat, TargetType)
from ..data.encounter_formations import BOSSES, SIMULATIONS, ZONES
from ..data.equipment import Equipment
from ..data.items import ITEM_PRICES
from ..data.monsters import get_monsters_dict
from ..errors import EventParsingError
from ..gamestate import GameState
from ..utils import search_strenum, stringify
from .advance_rng import AdvanceRNG
from .change_equipment import ChangeEquipment
from .change_party import ChangeParty
from .change_stat import ChangeStat
from .character_action import CharacterAction
from .comment import Comment
from .death import Death
from .encounter import (Encounter, MultizoneRandomEncounter, RandomEncounter,
                        SimulatedEncounter)
from .encounter_check import EncounterChecks
from .end_encounter import EndEncounter
from .escape import Escape
from .heal_party import Heal
from .kill import Bribe, Kill
from .main import Event
from .monster_action import MonsterAction
from .monster_spawn import MonsterSpawn
from .steal import Steal
from .yojimbo_turn import YojimboTurn


class ParsingFunction(Protocol):
    def __call__(self, gs: GameState, *args: str) -> Event:
        ...


def parse_amount(amount: str,
                 current_amount: int,
                 error_name: str = 'amount',
                 ) -> int:
    try:
        count = int(amount)
    except ValueError:
        raise EventParsingError(f'{error_name} must be an integer')
    if amount.startswith(('+', '-')):
        return count + current_amount
    return count


def parse_dict_key[K, V](key: K,
                         dict: dict[K, V],
                         error_name: str = 'key',
                         ) -> V:
    try:
        return dict[key]
    except KeyError:
        raise EventParsingError(f'No {error_name} named "{key}"')


def parse_enum_member[S: StrEnum](member_name: str,
                                  enum: type[S],
                                  enum_name: str = 'member',
                                  ) -> S:
    try:
        return search_strenum(enum, member_name)
    except ValueError:
        enum_members = ', '.join([stringify(m) for m in enum])
        text = f'{enum_name} can only be one of these values: {enum_members}'
        raise EventParsingError(text)


def parse_monster_slot(gs: GameState, slot: str) -> MonsterActor:
    try:
        index = int(slot[1]) - 1
    except ValueError:
        raise EventParsingError('Monster slot must be in the form m#')
    try:
        return gs.monster_party[index]
    except IndexError:
        raise EventParsingError(f'No monster in slot {index + 1}')


def parse_party_members_initials(party_members_initials: str,
                                 ) -> list[Character]:
    party_members = []
    initials = {stringify(c)[0]: c for c in tuple(Character)[:8]}
    for letter in party_members_initials:
        for initial in initials:
            if letter == initial:
                party_members.append(initials[initial])
                break
    # remove duplicates and keep order
    return list(dict.fromkeys(party_members))


def parse_equipment(equipment_type_name: str = '',
                    character_name: str = '',
                    slots: str = '',
                    *ability_names: str,
                    ) -> Equipment:
    equipment_type = parse_enum_member(
        equipment_type_name, EquipmentType, 'equipment type')

    character = parse_enum_member(character_name, Character, 'character')
    try:
        slots = int(slots)
    except ValueError:
        raise EventParsingError('Slots must be between 0 and 4')
    if not (0 <= slots <= 4):
        raise EventParsingError('Slots must be between 0 and 4')
    abilities = []
    for ability_name in ability_names:
        if len(abilities) >= 4:
            break
        ability = parse_enum_member(ability_name, Autoability, 'ability')
        if ability in abilities:
            continue
        abilities.append(ability)
    slots = max(slots, len(abilities))
    if character in (Character.VALEFOR, Character.SHIVA):
        base_weapon_damage = 14
    else:
        base_weapon_damage = 16
    equipment = Equipment(
        owner=character,
        type_=equipment_type,
        slots=slots,
        abilities=abilities,
        base_weapon_damage=base_weapon_damage,
        bonus_crit=3
        )
    return equipment


def parse_target(gs: GameState, target_name: str) -> Actor:
    if target_name in ('m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'):
        return parse_monster_slot(gs, target_name)
    elif target_name.endswith('_c'):
        char_name = target_name[:-2]
    elif target_name in get_monsters_dict():
        return MonsterActor(get_monsters_dict()[target_name])
    else:
        char_name = target_name
    try:
        char = search_strenum(Character, char_name)
    except ValueError:
        raise EventParsingError(f'"{target_name}" is not a valid target')
    return gs.characters[char]


def parse_encounter(gs: GameState,
                    name: str = '',
                    *zones: str,
                    ) -> Encounter | MultizoneRandomEncounter:
    if name in BOSSES:
        encounter_type = Encounter
    elif name in ZONES:
        encounter_type = RandomEncounter
    elif name in SIMULATIONS:
        encounter_type = SimulatedEncounter
    elif name == 'multizone':
        if not zones:
            raise EventParsingError
        for zone in zones:
            if zone not in ZONES:
                raise EventParsingError(f'No zone named "{zone}"')
        return MultizoneRandomEncounter(gs, zones)
    else:
        raise EventParsingError(f'No encounter named "{name}"')
    return encounter_type(gs, name)


def parse_encounter_count_change(gs: GameState,
                                 name: str = '',
                                 amount: str = '',
                                 *_,
                                 ) -> Comment:
    if name == 'total':
        count = parse_amount(amount, gs.encounters_count)
        gs.encounters_count = count
        count_name = 'Total'
    elif name == 'random':
        count = parse_amount(amount, gs.random_encounters_count)
        gs.random_encounters_count = count
        count_name = 'Random'
    elif name in ZONES:
        count = parse_amount(amount, gs.zone_encounters_counts[name])
        gs.zone_encounters_counts[name] = count
        count_name = ZONES[name].name
    else:
        raise EventParsingError
    return Comment(gs, f'{count_name} encounters count set to {count}')


def parse_steal(gs: GameState,
                monster_name: str = '',
                successful_steals: str = '0',
                *_,
                ) -> Steal:
    if not monster_name:
        raise EventParsingError
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    try:
        successful_steals = int(successful_steals)
    except ValueError:
        raise EventParsingError('successful steals must be an integer')
    if successful_steals < 0:
        raise EventParsingError(
            'successful steals must be greater or equal to 0')
    return Steal(gs, monster, successful_steals)


def parse_kill(gs: GameState,
               monster_name: str = '',
               killer_name: str = '',
               ap_characters_string: str = '',
               overkill: str = '',
               *_,
               ) -> Kill:
    if not monster_name or not killer_name:
        raise EventParsingError
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    killer = parse_enum_member(killer_name, Character, 'killer')
    ap_characters = parse_party_members_initials(ap_characters_string)
    if overkill in ('overkill', 'ok'):
        kill_type = KillType.OVERKILL
    else:
        kill_type = KillType.NORMAL
    return Kill(gs, monster, killer, ap_characters, kill_type)


def parse_bribe(gs: GameState,
                monster_name: str = '',
                user_name: str = '',
                ap_characters_string: str = '',
                *_,
                ) -> Bribe:
    if not monster_name or not user_name:
        raise EventParsingError
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    user = parse_enum_member(user_name, Character, 'user')
    ap_characters = parse_party_members_initials(ap_characters_string)
    return Bribe(gs, monster, user, ap_characters)


def parse_death(gs: GameState, character_name: str = 'unknown', *_) -> Death:
    try:
        character = search_strenum(Character, character_name)
    except ValueError:
        character = Character.UNKNOWN
    return Death(gs, character)


def parse_roll(gs: GameState,
               rng_index: str = '',
               amount: str = '1',
               *_,
               ) -> AdvanceRNG:
    try:
        if rng_index.startswith('rng'):
            rng_index = int(rng_index[3:])
        else:
            rng_index = int(rng_index)
        amount = int(amount)
    except ValueError:
        raise EventParsingError('rng needs to be an integer')
    try:
        amount = int(amount)
    except ValueError:
        raise EventParsingError('amount needs to be an integer')
    if amount < 0:
        raise EventParsingError('amount needs to be an greater or equal to 0')
    if not (0 <= rng_index < 68):
        raise EventParsingError(f'Can\'t advance rng index {rng_index}')
    if amount > 100000:
        raise EventParsingError('Can\'t advance rng more than 100000 times')
    return AdvanceRNG(gs, rng_index, amount)


def parse_party_change(gs: GameState,
                       party_formation_string: str = '',
                       *_,
                       ) -> ChangeParty:
    if not party_formation_string:
        raise EventParsingError
    party_formation = parse_party_members_initials(party_formation_string)

    if not party_formation:
        raise EventParsingError(
            f'no characters initials in "{party_formation_string}"')
    return ChangeParty(gs, party_formation)


def parse_summon(gs: GameState, aeon_name: str = '', *_) -> ChangeParty:
    if not aeon_name:
        raise EventParsingError
    if 'magus_sisters'.startswith(aeon_name):
        party_formation = [Character.CINDY, Character.SANDY, Character.MINDY]
    else:
        for aeon in tuple(Character)[8:]:
            if stringify(aeon).startswith(aeon_name):
                party_formation = [aeon]
                break
        else:
            raise EventParsingError(f'No aeon named "{aeon_name}"')
    return ChangeParty(gs, party_formation)


def parse_action(gs: GameState,
                 character_name: str = '',
                 action_name: str = '',
                 target_name: str = '',
                 od_time_remaining: str = '',
                 od_n_of_hits: str = '',
                 *_,
                 ) -> CharacterAction | Escape:
    if not character_name or not action_name:
        raise EventParsingError
    character = parse_enum_member(character_name, Character, 'character')
    actor = gs.characters[character]

    if action_name == 'escape':
        return Escape(gs, actor)

    action = parse_dict_key(action_name, ACTIONS, 'action')
    if not action.can_use_in_combat:
        raise EventParsingError(f'Action {action} can\'t be used in battle')

    match action.target:
        case TargetType.SINGLE if not target_name:
            text = (f'Action "{action}" requires a target '
                    '(Character/Monster/Monster Slot)')
            raise EventParsingError(text)
        case TargetType.SINGLE_CHARACTER if not target_name:
            text = f'Action "{action}" requires a target (Character)'
            raise EventParsingError(text)
        case TargetType.SINGLE_MONSTER if not target_name:
            text = f'Action "{action}" requires a target (Monster/Monster Slot)'
            raise EventParsingError(text)
        case TargetType.PARTY if not target_name:
            text = (f'Action "{action}" requires a target '
                    '(Character/Monster/Monster Slot/"monsters"/"party")')
            raise EventParsingError(text)
        case TargetType.SINGLE:
            target = parse_target(gs, target_name)
        case TargetType.SINGLE_CHARACTER:
            if target_name.endswith('_c'):
                target_name = target_name[:-2]
            char = parse_enum_member(target_name, Character, 'target')
            target = gs.characters[char]
        case TargetType.SINGLE_MONSTER:
            if target_name in ('m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'):
                target = parse_monster_slot(gs, target_name)
            else:
                monster = parse_dict_key(
                    target_name, get_monsters_dict(), 'monster name or slot')
                target = MonsterActor(monster)
        case TargetType.PARTY:
            if target_name == 'party':
                target = TargetType.CHARACTERS_PARTY
            elif target_name == 'monsters':
                target = TargetType.MONSTERS_PARTY
            else:
                target = parse_target(gs, target_name)
        case (TargetType.CHARACTERS_PARTY
              | TargetType.MONSTERS_PARTY
              | TargetType.RANDOM_CHARACTER
              | TargetType.RANDOM_MONSTER) if target_name:
            try:
                target = parse_target(gs, target_name)
            except EventParsingError:
                target = action.target
        case MonsterSlot() as slot:
            try:
                target = gs.monster_party[slot]
            except IndexError:
                raise EventParsingError(f'No monster in slot {int(slot)}')
        case Character() as char:
            target = gs.characters[char]
        case _:
            target = action.target

    match action.overdrive_user:
        case Character.TIDUS | Character.AURON | Character.WAKKA:
            try:
                time = float(target_name)
            except ValueError:
                try:
                    time = float(od_time_remaining)
                except ValueError:
                    time = 0
                if od_n_of_hits.isdecimal():
                    n_of_hits = int(od_n_of_hits)
                else:
                    n_of_hits = 1
            else:
                if od_time_remaining.isdecimal():
                    n_of_hits = int(od_time_remaining)
                elif od_n_of_hits.isdecimal():
                    n_of_hits = int(od_n_of_hits)
                else:
                    n_of_hits = 1
        case Character.LULU:
            time = 0
            if target_name.isdecimal():
                n_of_hits = int(target_name)
            elif od_time_remaining.isdecimal():
                n_of_hits = int(od_time_remaining)
            elif od_n_of_hits.isdecimal():
                n_of_hits = int(od_n_of_hits)
            else:
                n_of_hits = 1
        case _:
            time = 0
            n_of_hits = 1
    time = int(time * 1000)
    return CharacterAction(gs, actor, action, target, time, n_of_hits)


def parse_stat_update(gs: GameState,
                      actor_name: str = '',
                      stat_name: str = '',
                      amount: str = '',
                      *_,
                      ) -> ChangeStat | Comment:
    if not actor_name:
        raise EventParsingError
    if actor_name in ('m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'):
        actor = parse_monster_slot(gs, actor_name)
    else:
        try:
            actor = search_strenum(Character, actor_name)
        except ValueError:
            raise EventParsingError(f'"{actor_name}" is not a valid actor')
        actor = gs.characters[actor]
    if not stat_name and not amount:
        stats = [f'{SHORT_STATS_NAMES[s]} {v}' for s, v in actor.stats.items()]
        text = f'Stats: {actor} | {' | '.join(stats)}'
        return Comment(gs, text)
    if stat_name == 'ctb':
        actor.ctb = parse_amount(amount, actor.ctb)
        return Comment(gs, f'{actor}\'s CTB changed to {actor.ctb}')
    stat = parse_enum_member(stat_name, Stat, 'stat')
    stat_value = parse_amount(amount, actor.stats[stat])
    return ChangeStat(gs, actor, stat, stat_value)


def parse_yojimbo_action(gs: GameState,
                         action_name: str = '',
                         monster_name: str = '',
                         overdrive: str = '',
                         *_,
                         ) -> YojimboTurn:
    if not action_name or not monster_name:
        raise EventParsingError
    action = parse_dict_key(action_name, YOJIMBO_ACTIONS, 'yojimbo action')
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    overdrive = overdrive == 'overdrive'
    return YojimboTurn(gs, action, monster, overdrive)


def parse_compatibility_update(gs: GameState,
                               compatibility: str = '',
                               *_,
                               ) -> Comment:
    old_compatibility = gs.compatibility
    gs.compatibility = parse_amount(
        compatibility, gs.compatibility, 'compatibility')
    text = f'Compatibility: {old_compatibility} -> {gs.compatibility}'
    return Comment(gs, text)


def parse_monster_action(gs: GameState,
                         monster_name: str = '',
                         action_name: str = '',
                         *_,
                         ) -> MonsterAction:
    if not monster_name:
        raise EventParsingError

    if monster_name in ('m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'):
        actor = parse_monster_slot(gs, monster_name)
    else:
        monster = parse_dict_key(
            monster_name, get_monsters_dict(), 'monster name or slot')
        actor = MonsterActor(monster)
    if action_name == 'does_nothing':
        action = ACTIONS['does_nothing']
    elif action_name == 'forced_action':
        action = actor.monster.forced_action
    elif not action_name and len(actor.monster.actions) == 1:
        action = next(iter(actor.monster.actions.values()))
    else:
        try:
            action = actor.monster.actions[action_name]
        except KeyError:
            text = (f'Available actions for {actor}: '
                    f'{', '.join(a for a in actor.monster.actions)}'
                    ', does_nothing, forced_action')
            raise EventParsingError(text)

    if not action.can_use_in_combat:
        raise EventParsingError(f'Action {action} can\'t be used in battle')
    return MonsterAction(gs, actor, action, None)


def parse_equipment_change(gs: GameState,
                           equipment_type_name: str = '',
                           character_name: str = '',
                           slots: str = '',
                           *ability_names: str,
                           ) -> ChangeEquipment:
    if not all((equipment_type_name, character_name, slots)):
        raise EventParsingError
    equipment = parse_equipment(
        equipment_type_name, character_name, slots, *ability_names)
    return ChangeEquipment(gs, equipment)


def parse_end_encounter(gs: GameState, *_) -> EndEncounter:
    return EndEncounter(gs)


def parse_heal(gs: GameState,
               character_name: str = '',
               amount: str = '99999',
               *_) -> Heal:
    if character_name:
        characters = [parse_enum_member(character_name, Character, 'character')]
    else:
        characters = list(Character)
    try:
        amount = int(amount)
    except ValueError:
        amount = 99999

    return Heal(gs, characters, amount)


def parse_character_ap(gs: GameState,
                       character_name: str = '',
                       amount: str = '0',
                       *_) -> Comment:
    if character_name:
        characters = [parse_enum_member(character_name, Character, 'character')]
    else:
        characters = list(Character)[:7]
    try:
        amount = int(amount)
    except ValueError:
        amount = 0
    lines = []
    for character in characters:
        actor = gs.characters[character]
        if amount:
            actor.ap += amount
            added_ap = f' (added {amount} AP)'
        else:
            added_ap = ''
        next_s_lv_ap = (
            s_lv_to_total_ap(actor.s_lv + 1, actor.defaults.starting_s_lv)
            - actor.ap
            )
        lines.append(f'{actor.character}: {actor.s_lv} S. Lv '
                     f'({actor.ap} AP Total, {next_s_lv_ap} for next level)'
                     f'{added_ap}')
    return Comment(gs, '\n'.join(lines))


def parse_actor_status(gs: GameState,
                       actor_name: str = '',
                       *_) -> Comment:
    if not actor_name:
        raise EventParsingError
    if actor_name in ('m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'):
        actor = parse_monster_slot(gs, actor_name)
    else:
        try:
            character = search_strenum(Character, actor_name)
        except ValueError:
            raise EventParsingError(f'"{actor_name}" is not a valid actor')
        actor = gs.characters[character]
    text = f'Status: {actor} {actor.current_hp}/{actor.max_hp} HP'
    statuses = [f'{s} ({stacks})' for s, stacks in actor.statuses.items()]
    if statuses:
        text += f' | Statuses: {', '.join(statuses)}'
    buffs = [f'{b} ({stacks})' for b, stacks in actor.buffs.items() if stacks]
    if buffs:
        text += f' | Buffs: {', '.join(statuses)}'
    return Comment(gs, text)


def parse_monster_spawn(gs: GameState,
                        monster_name: str = '',
                        slot: str = '',
                        forced_ctb: str = '',
                        *_) -> Comment:
    if not monster_name or not slot:
        raise EventParsingError
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    try:
        slot = int(slot)
    except ValueError:
        raise EventParsingError('Slot must be an integer')
    slot_limit = min(len(gs.monster_party) + 1, 8)
    if not (1 <= slot <= slot_limit):
        raise EventParsingError(f'Slot must be between 1 and {slot_limit}')
    slot = MonsterSlot(slot - 1)
    try:
        forced_ctb = int(forced_ctb)
    except ValueError:
        forced_ctb = None
    return MonsterSpawn(gs, monster, slot, forced_ctb)


def parse_monster_elemental_affinities_change(gs: GameState,
                                              monster_slot: str = '',
                                              element_name: str = '',
                                              affinity_name: str = '',
                                              *_) -> Comment:
    if not all((monster_slot, element_name, affinity_name)):
        raise EventParsingError
    actor = parse_monster_slot(gs, monster_slot)
    element = parse_enum_member(element_name, Element, 'element')
    affinity = parse_enum_member(affinity_name, ElementalAffinity, 'affinity')
    actor.elemental_affinities[element] = affinity
    text = f'Elemental affinity to {element} of {actor} changed to {affinity}'
    return Comment(gs, text)


def parse_encounter_checks(gs: GameState,
                           zone_name: str = '',
                           steps: str = '',
                           continue_zone: str = '',
                           *_) -> EncounterChecks:
    if not zone_name or not steps:
        raise EventParsingError

    zone = parse_dict_key(zone_name, ZONES, 'zone')
    try:
        distance = int(steps) * 10
    except ValueError:
        raise EventParsingError('Step must be an integer')
    continue_previous_zone = continue_zone == 'true'
    return EncounterChecks(gs, zone, distance, continue_previous_zone)


def parse_inventory_command(gs: GameState,
                            command: str = '',
                            *params: str,
                            ) -> Comment:
    match [command, *params]:
        case ('show', *_):
            if params and params[0] == 'equipment':
                text = 'Equipment: '
                lines = [f'#{i} {e}'
                         for i, e in enumerate(gs.equipment_inventory, 1)]
                if not lines:
                    lines.append('Empty')
                text += '\n           '.join(lines)
            elif params and params[0] == 'gil':
                text = f'Gil: {gs.gil}\n'
            else:
                text = gs.inventory.to_string()
        case ('get' | 'use', 'gil', amount, *_):
            try:
                gil = int(amount)
            except ValueError:
                raise EventParsingError('Gil amount needs to be an integer')
            if gil < 1:
                raise EventParsingError('Gil amount needs to be more than 0')
            if command == 'use':
                if gil > gs.gil:
                    raise EventParsingError(
                        f'Not enough gil (need {gil - gs.gil} more)')
                gs.gil -= gil
                text = f'Used {gil} Gil ({gs.gil} Gil total)'
            else:
                gs.gil += gil
                text = f'Added {gil} Gil ({gs.gil} Gil total)'
        case ('get' | 'use', 'gil', *_):
            raise EventParsingError(f'Usage: inventory {command} gil [amount]')
        case ('get' | 'buy', 'equipment', equip_type, character, slots, *abilities):
            equip = parse_equipment(equip_type, character, slots, *abilities)
            if command == 'get':
                text = f'Added {equip}'
            else:
                gil = equip.gil_value
                if gil > gs.gil:
                    raise EventParsingError(
                        f'Not enough gil (need {gil - gs.gil} more)')
                gs.gil -= gil
                text = f'Bought {equip} for {gil} gil'
            gs.add_to_equipment_inventory(equip)
        case ('get' | 'buy', 'equipment', *_):
            usage = (f'Usage: inventory {command} equipment [equip type] '
                     '[character] [slots] (abilities)')
            raise EventParsingError(usage)
        case ('sell', 'equipment', equip_slot, *_) if equip_slot.isdecimal():
            if not gs.equipment_inventory:
                raise EventParsingError('Equipment inventory is empty')
            equip_index = int(equip_slot) - 1
            if not (0 <= equip_index < len(gs.equipment_inventory)):
                raise EventParsingError('Equipment slot needs to be between 1'
                                        f' and {len(gs.equipment_inventory)}')
            equip = gs.equipment_inventory[equip_index]
            if equip is None:
                raise EventParsingError(f'Slot {equip_slot} is empty')
            gs.gil += equip.sell_value
            gs.equipment_inventory[equip_index] = None
            gs.clean_equipment_inventory()
            text = f'Sold {equip}'
        case ('sell', 'equipment', equip_type, character, slots, *abilities):
            equip = parse_equipment(equip_type, character, slots, *abilities)
            gs.gil += equip.sell_value
            text = f'Sold {equip}'
        case ('sell', 'equipment', 'weapon' | 'armor', *_):
            usage = ('Usage: inventory sell equipment [equip type] '
                     '[character] [slots] (abilities)')
            raise EventParsingError(usage)
        case ('sell', 'equipment', *_):
            usage = 'Usage: inventory sell equipment [equipment slot]'
            raise EventParsingError(usage)
        case ('get' | 'buy' | 'use' | 'sell', item_name, amount, *_):
            item = parse_enum_member(item_name, Item, 'item')
            try:
                amount = int(amount)
            except ValueError:
                raise EventParsingError('Amount needs to be an integer')
            if amount < 1:
                raise EventParsingError('Amount needs to be more than 0')
            if command == 'get':
                gs.inventory.add(item, amount)
                text = f'Added {item} x{amount} to inventory'
            elif command == 'buy':
                gil = ITEM_PRICES[item] * amount
                if gil > gs.gil:
                    raise EventParsingError('Not enough gil '
                                            f'(need {gil - gs.gil} more)')
                gs.gil -= gil
                gs.inventory.add(item, amount)
                text = f'Bought {item} x{amount} for {gil} gil'
            else:
                try:
                    gs.inventory.remove(item, amount)
                except ValueError as error:
                    raise EventParsingError(str(error))
                if command == 'use':
                    text = f'Used {item} x{amount}'
                else:
                    gil = max(1, (ITEM_PRICES[item] // 4)) * amount
                    gs.gil += gil
                    text = f'Sold {item} x{amount} for {gil} gil'
                amount = amount * -1
        case ('get' | 'buy' | 'use' | 'sell', *_):
            usage = f'Usage: inventory {command} [item] [amount]'
            raise EventParsingError(usage)
        case ('switch', slot_1_index, slot_2_index, *_):
            try:
                slot_1_index = int(slot_1_index) - 1
                slot_2_index = int(slot_2_index) - 1
            except ValueError:
                raise EventParsingError('Inventory slot needs to be an integer')
            try:
                gs.inventory.switch(slot_1_index, slot_2_index)
            except ValueError:
                raise EventParsingError('Inventory slot needs to be between'
                                        f' 1 and {len(gs.inventory)}')
            item_1 = gs.inventory[slot_1_index][0]
            item_2 = gs.inventory[slot_2_index][0]
            text = (f'Switched {item_2} (slot {slot_1_index + 1})'
                    f' for {item_1} (slot {slot_2_index + 1})')
        case ('switch', *_):
            usage = 'Usage: inventory switch [slot 1] [slot 2]'
            raise EventParsingError(usage)
        case ('autosort', *_):
            gs.inventory.autosort()
            text = 'Autosorted inventory'
        case _:
            raise EventParsingError
    return Comment(gs, text)


USAGE: dict[ParsingFunction, list[str]] = {
    parse_encounter: [
        'encounter (preemp/ambush/simulated/name/zone)',
        # 'encounter multizone [zones]',  # undocumented
        ],
    parse_encounter_count_change: [
        'encounters_count [total/random/zone name] [(+/-)amount]',
        ],
    parse_steal: [
        'steal [monster name] (successful steals)',
        ],
    parse_kill: [
        'kill [monster name] [killer] (characters initials) (overkill/ok)',
    ],
    parse_bribe: [
        'bribe [monster name] [user] (characters initials)',
    ],
    parse_death: [
        'death (character)',
    ],
    parse_roll: [
        'roll [rng#] [amount]',
        'waste [rng#] [amount]',
        'advance [rng#] [amount]',
    ],
    parse_party_change: [
        'party [characters initials]',
    ],
    parse_summon: [
        'summon [aeon name]',
    ],
    parse_action: [
        'action [character] [action] [target]',
        'action [character] [action (aoe)] (target/party/monsters)',
        'action [character] [action (od)] [target] (time remaining)',
        'action [character] [action (aoe od)] (time remaining)',
        'action [character] attack_reels (time remaining) (# of hits)',
        'action [character] [fury] (# of hits)',
    ],
    parse_stat_update: [
        'stat [character/monster slot] (stat) [(+/-)amount]',
    ],
    parse_yojimbo_action: [
        'yojimboturn [action] [monster] (overdrive)',
    ],
    parse_compatibility_update: [
        'compatibility [(+/-)amount]',
    ],
    parse_monster_action: [
        'monsteraction [monster slot/name] (action)',
    ],
    parse_equipment_change: [
        'equip [equip type] [character] [# of slots] (abilities)',
    ],
    parse_end_encounter: [
        'endencounter',
    ],
    parse_heal: [
        'heal (character) (amount)',
    ],
    parse_character_ap: [
        'ap (character) ((+/-)amount)',
    ],
    parse_actor_status: [
        'status [character/monster slot]',
    ],
    parse_monster_spawn: [
        'spawn [monster name] [slot] (forced ctb)',
    ],
    parse_monster_elemental_affinities_change: [
        'element [monster slot] [element] [affinity]',
    ],
    parse_encounter_checks: [
        'walk [zone] [steps]',
    ],
    parse_inventory_command: [
        'inventory [show/get/buy/use/sell/switch/autosort] [...]',
        'inventory show (equipment/gil)',
        'inventory [get/buy/use/sell] [item] [amount]',
        'inventory [get/use] gil [amount]',
        'inventory [get/buy/sell] equipment [equip type] [character] [slots] (abilities)',
        'inventory sell equipment [equipment slot]',
        'inventory switch [slot 1] [slot 2]',
        'inventory autosort',
    ],
}
