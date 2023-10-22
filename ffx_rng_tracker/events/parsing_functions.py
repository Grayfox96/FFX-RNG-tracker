from typing import Callable

from ..data.actions import ACTIONS, YOJIMBO_ACTIONS
from ..data.characters import s_lv_to_total_ap
from ..data.constants import (SHORT_STATS_NAMES, Autoability, Character,
                              EquipmentType, Item, MonsterSlot, Stat,
                              StringEnum, TargetType)
from ..data.encounter_formations import BOSSES, SIMULATIONS, ZONES
from ..data.equipment import Equipment
from ..data.items import ITEM_PRICES
from ..data.monsters import MonsterState, get_monsters_dict
from ..errors import EventParsingError
from ..gamestate import GameState
from ..ui_functions import get_inventory_table
from ..utils import search_stringenum, stringify
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

ParsingFunction = (Callable[[GameState, str], Event]
                   | Callable[[GameState, str, str], Event]
                   | Callable[[GameState, str, str, str], Event]
                   | Callable[..., Event]
                   )


def parse_dict_key[K, V](key: K,
                         dict: dict[K, V],
                         error_name: str = 'key',
                         ) -> V:
    try:
        return dict[key]
    except KeyError:
        raise EventParsingError(f'No {error_name} named "{key}"')


def parse_enum_member[S: StringEnum](member_name: str,
                                     enum: type[S],
                                     enum_name: str = 'member',
                                     ) -> S:
    try:
        return search_stringenum(enum, member_name)
    except ValueError:
        raise EventParsingError(f'No {enum_name} named "{member_name}"')


def parse_monster_slot(gs: GameState, slot: str) -> MonsterState:
    try:
        index = int(slot[1:]) - 1
    except ValueError:
        raise EventParsingError('Monster slot must be in the form m#')
    try:
        return gs.monster_party[index]
    except IndexError:
        raise EventParsingError(f'No monster in slot {index + 1}')


def parse_party_members_initials(party_members_initials: str,
                                 ) -> list[Character]:
    party_members = []
    for letter in party_members_initials:
        for character in tuple(Character)[:8]:
            if letter == stringify(character)[0]:
                party_members.append(character)
                break
    # remove duplicates and keep order
    return list(dict.fromkeys(party_members))


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
    usage = 'Usage: encounters_count [total/random/zone name] [(+/-) amount]'
    if not name:
        raise EventParsingError(usage)
    try:
        count = int(amount)
    except ValueError:
        raise EventParsingError('Amount must be an integer.')

    if name == 'total':
        if amount.startswith(('+', '-')):
            gs.encounters_count += count
            count = gs.encounters_count
        else:
            gs.encounters_count = count
        count_name = 'Total'
    elif name == 'random':
        if amount.startswith(('+', '-')):
            gs.random_encounters_count += count
            count = gs.random_encounters_count
        else:
            gs.random_encounters_count = count
        count_name = 'Random'
    elif name in ZONES:
        if amount.startswith(('+', '-')):
            gs.zone_encounters_counts[name] += count
            count = gs.zone_encounters_counts[name]
        else:
            gs.zone_encounters_counts[name] = count
        count_name = ZONES[name].name
    else:
        raise EventParsingError(usage)
    return Comment(gs, f'{count_name} encounters count set to {count}')


def parse_steal(gs: GameState,
                monster_name: str = '',
                successful_steals: str = '0',
                *_,
                ) -> Steal:
    usage = 'Usage: steal [monster_name] (successful steals)'
    if not monster_name:
        raise EventParsingError(usage)
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    try:
        successful_steals = int(successful_steals)
    except ValueError:
        raise EventParsingError('"successful steals" must be an integer')
    return Steal(gs, monster, successful_steals)


def parse_kill(gs: GameState,
               monster_name: str = '',
               killer_name: str = '',
               ap_characters_string: str = '',
               overkill: str = '',
               *_,
               ) -> Kill:
    usage = ('Usage: kill [monster_name] [killer] (party members initials) '
             '(overkill/ok)')
    if not monster_name or not killer_name:
        raise EventParsingError(usage)
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    killer = parse_enum_member(killer_name, Character, 'character')
    ap_characters = parse_party_members_initials(ap_characters_string)
    overkill = overkill in ('overkill', 'ok')
    return Kill(gs, monster, killer, ap_characters, overkill)


def parse_bribe(gs: GameState,
                monster_name: str = '',
                user_name: str = '',
                *_,
                ) -> Bribe:
    usage = 'Usage: bribe [monster_name] [user]'
    if not monster_name or not user_name:
        raise EventParsingError(usage)
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    user = parse_enum_member(user_name, Character, 'character')
    return Bribe(gs, monster, user)


def parse_death(gs: GameState, character_name: str = 'unknown', *_) -> Death:
    try:
        character = search_stringenum(Character, character_name)
    except ValueError:
        character = Character.UNKNOWN
    return Death(gs, character)


def parse_roll(gs: GameState,
               rng_index: str = '',
               times: str = '1',
               *_,
               ) -> AdvanceRNG:
    usage = 'Usage: waste/advance/roll [rng#] [amount]'
    try:
        if rng_index.startswith('rng'):
            rng_index = int(rng_index[3:])
        else:
            rng_index = int(rng_index)
        times = int(times)
    except ValueError:
        raise EventParsingError(usage)
    if not (0 <= rng_index < 68):
        raise EventParsingError(f'Can\'t advance rng index {rng_index}')
    if times > 100000:
        raise EventParsingError('Can\'t advance rng more than 100000 times.')
    return AdvanceRNG(gs, rng_index, times)


def parse_party_change(gs: GameState,
                       party_formation_string: str = '',
                       *_,
                       ) -> ChangeParty:
    usage = 'Usage: party [party members initials]'
    if not party_formation_string:
        raise EventParsingError(usage)
    party_formation = parse_party_members_initials(party_formation_string)

    if not party_formation:
        raise EventParsingError(usage)
    return ChangeParty(gs, party_formation)


def parse_summon(gs: GameState,
                 aeon_name: str = '',
                 *_,
                 ) -> ChangeParty:
    usage = 'Usage: summon [aeon name]'
    if not aeon_name:
        raise EventParsingError(usage)
    if 'magus_sisters'.startswith(aeon_name):
        party_formation = [Character.CINDY, Character.SANDY, Character.MINDY]
    else:
        for aeon in tuple(Character)[8:]:
            if stringify(aeon).startswith(aeon_name):
                party_formation = [aeon]
                break
        else:
            raise EventParsingError(usage)
    return ChangeParty(gs, party_formation)


def parse_action(gs: GameState,
                 character_name: str = '',
                 action_name: str = '',
                 target_name: str = '',
                 time_remaining: str = '0',
                 *_,
                 ) -> CharacterAction | Escape:
    usage = 'Usage: [character] [action name] (target)'
    if not character_name or not action_name:
        raise EventParsingError(usage)
    character = parse_enum_member(character_name, Character, 'character')
    character = gs.characters[character]

    if action_name == 'escape':
        return Escape(gs, character)

    action = parse_dict_key(action_name, ACTIONS, 'action')

    if action.target is TargetType.SELF:
        target = character
    elif target_name in ('m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'):
        target = parse_monster_slot(gs, target_name)
    elif target_name.endswith('_c'):
        target = parse_enum_member(target_name[:-2], Character, 'character')
        target = gs.characters[target]
    elif target_name:
        monsters = get_monsters_dict()
        try:
            target = MonsterState(monsters[target_name])
        except KeyError:
            target = parse_enum_member(target_name, Character, 'character')
            target = gs.characters[target]
    else:
        raise EventParsingError(f'Action "{action}" requires a target.')

    try:
        time_remaining = float(time_remaining)
    except ValueError:
        time_remaining = 0
    time_remaining = int(time_remaining * 1000)
    return CharacterAction(gs, character, action, target, time_remaining)


def parse_stat_update(gs: GameState,
                      target_name: str = '',
                      stat_name: str = '',
                      amount: str = '',
                      *_,
                      ) -> ChangeStat | Comment:
    usage = 'Usage: stat [character/monster slot] [stat] [(+/-) amount]'
    if not target_name:
        raise EventParsingError(usage)
    if target_name in ('m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'):
        target = parse_monster_slot(gs, target_name)
    else:
        target = parse_enum_member(
            target_name, Character, 'character or monster slot')
        target = gs.characters[target]
    if not stat_name and not amount:
        text = f'{target} Stats: ' + ' / '.join(
            [f'{SHORT_STATS_NAMES[s]} {v}' for s, v in target.stats.items()])
        return Comment(gs, text)
    if stat_name == 'ctb':
        try:
            if amount.startswith(('+', '-')):
                target.ctb += int(amount)
            else:
                target.ctb = int(amount)
        except ValueError:
            raise EventParsingError('Stat value must be an integer.')
        gs.normalize_ctbs(gs.get_min_ctb())
        return Comment(gs, f'{target}\'s CTB changed to {target.ctb}')
    stat = parse_enum_member(stat_name, Stat, 'stat')
    stat_value = target.stats[stat]
    try:
        if amount.startswith(('+', '-')):
            stat_value += int(amount)
        else:
            stat_value = int(amount)
    except ValueError:
        raise EventParsingError('Stat value must be an integer.')
    return ChangeStat(gs, target, stat, stat_value)


def parse_yojimbo_action(gs: GameState,
                         action_name: str = '',
                         monster_name: str = '',
                         overdrive: str = '',
                         *_,
                         ) -> YojimboTurn:
    usage = 'Usage: [action] [monster] (overdrive)'
    if not action_name or not monster_name:
        raise EventParsingError(usage)
    action = parse_dict_key(action_name, YOJIMBO_ACTIONS, 'Yojimbo action')
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    overdrive = overdrive == 'overdrive'
    return YojimboTurn(gs, action, monster, overdrive)


def parse_compatibility_update(gs: GameState,
                               compatibility: str = '',
                               *_,
                               ) -> Comment:
    usage = 'Usage: compatibility [(+/-)amount]'
    try:
        if compatibility.startswith(('+', '-')):
            gs.compatibility += int(compatibility)
        else:
            gs.compatibility = int(compatibility)
    except ValueError:
        raise EventParsingError(usage)
    return Comment(gs, f'Compatibility changed to {gs.compatibility}')


def parse_monster_action(gs: GameState,
                         monster_name: str = '',
                         action_name: str = '',
                         *_,
                         ) -> MonsterAction:
    usage = 'Usage: monsteraction [monster slot/name] [action_name]'
    if not monster_name:
        raise EventParsingError(usage)

    if monster_name in ('m1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8'):
        monster = parse_monster_slot(gs, monster_name)
    else:
        monster = MonsterState(
            parse_dict_key(monster_name, get_monsters_dict(), 'monster'))
    try:
        action = monster.monster.actions[action_name]
    except KeyError:
        action_names = ', '.join(str(a) for a in monster.monster.actions)
        raise EventParsingError(f'Available actions for {monster}: '
                                f'{action_names}')
    return MonsterAction(gs, monster, action)


def parse_equipment_change(gs: GameState,
                           equipment_type_name: str = '',
                           character_name: str = '',
                           slots: str = '',
                           *ability_names: str,
                           ) -> ChangeEquipment:
    usage = 'Usage: equip [equip_type] [character] [slots] (abilities)'
    if not all((equipment_type_name, character_name, slots)):
        raise EventParsingError(usage)
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
    for autoability_name in ability_names:
        if len(abilities) >= 4:
            break
        autoability = parse_enum_member(
            autoability_name, Autoability, 'autoability')
        if autoability in abilities:
            continue
        abilities.append(autoability)
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
    return ChangeEquipment(gs, equipment)


def parse_end_encounter(gs: GameState, *_) -> EndEncounter:
    return EndEncounter(gs)


def parse_heal(gs: GameState,
               character_name: str = '',
               amount: str = '99999',
               *_) -> Heal:
    characters = []
    if character_name:
        characters.append(
            parse_enum_member(character_name, Character, 'character'))
    else:
        characters.extend(tuple(Character))
    try:
        amount = int(amount)
    except ValueError:
        amount = 99999

    return Heal(gs, characters, amount)


def parse_character_ap(gs: GameState,
                       character_name: str = '',
                       *_) -> Comment:
    usage = 'Usage: ap (character)'
    if character_name:
        characters = [parse_enum_member(character_name, Character, 'character')]
    else:
        characters = tuple(Character)[:7]
    lines = []
    for character in characters:
        state = gs.characters[character]
        next_s_lv_ap = (
            s_lv_to_total_ap(state.s_lv + 1, state.defaults.starting_s_lv)
            - state.ap
            )
        lines.append(f'{state.character}: {state.s_lv} S. Lv '
                     f'({state.ap} AP Total, {next_s_lv_ap} for next level)')
    return Comment(gs, '\n'.join(lines))


def parse_character_status(gs: GameState,
                           character_name: str = '',
                           *_) -> Comment:
    usage = 'Usage: status [character]'
    if not character_name:
        raise EventParsingError(usage)
    char = parse_enum_member(character_name, Character, 'character')
    char = gs.characters[char]
    text = f'{char}: hp {char.current_hp}, statuses {char.statuses}'
    return Comment(gs, text)


def parse_monster_spawn(gs: GameState,
                        monster_name: str = '',
                        slot: str = '',
                        forced_ctb: str = '0',
                        *_) -> Comment:
    usage = 'spawn [monster_name] [slot] (forced ctb)'
    if not monster_name or not slot:
        raise EventParsingError(usage)
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
        forced_ctb = 0
    return MonsterSpawn(gs, monster, slot, forced_ctb)


def parse_encounter_checks(gs: GameState,
                           zone_name: str = '',
                           steps: str = '',
                           continue_zone: str = '',
                           *_) -> EncounterChecks:
    usage = 'walk [zone] [steps]'
    if not zone_name or not steps:
        raise EventParsingError(usage)

    zone = parse_dict_key(zone_name, ZONES, 'zone')
    try:
        distance = int(steps) * 10
    except ValueError:
        raise EventParsingError('Step must be an integer')
    continue_previous_zone = continue_zone == 'true'
    return EncounterChecks(gs, zone, distance, continue_previous_zone)


def parse_inventory_command(gs: GameState,
                            command: str = '',
                            *params) -> Comment:
    match command:
        case 'show':
            show_equipment = bool(params) and params[0] == 'equipment'
            if show_equipment:
                text = 'Equipment: '
                text += '\n           '.join(
                    [str(e) for e in gs.equipment_inventory])
            else:
                text = f'Gil: {gs.gil}\n'
                text += get_inventory_table(gs.inventory)
        case 'use' | 'get' | 'buy' | 'sell':
            usage = f'Usage: inventory {command} [item name] [quantity]'
            try:
                item_name, quantity, *_ = params
                item = search_stringenum(Item, item_name)
                quantity = int(quantity)
            except ValueError:
                raise EventParsingError(usage)
            if quantity < 1:
                raise EventParsingError(
                    f'Can\'t {command} a negative quantity of items')
            if command == 'buy':
                gil = ITEM_PRICES[item] * quantity
                if gil > gs.gil:
                    raise EventParsingError('Not enough gil')
                gs.gil -= gil
                text = f'Bought {item} x{quantity} with {gil} gil'
            elif command == 'sell':
                items = [s.item for s in gs.inventory]
                if item not in items:
                    raise EventParsingError(f'{item} is not in the inventory')
                slot = gs.inventory[items.index(item)]
                if quantity > slot.quantity:
                    raise EventParsingError(f'Not enough {item} to sell')
                gil = max(1, (ITEM_PRICES[item] // 4)) * quantity
                gs.gil += gil
                text = f'Sold {item} x{quantity} for {gil} gil'
                quantity = quantity * -1
            elif command == 'use':
                text = f'Used {item} x{quantity}'
                quantity = quantity * -1
            else:
                text = f'Added {item} x{quantity} to inventory'
            gs.add_to_inventory(item, quantity)
        case 'switch':
            usage = f'Usage: inventory {command} [slot 1] [slot 2]'
            try:
                slot_1_index, slot_2_index, *_ = params
                slot_1_index = int(slot_1_index)
                slot_2_index = int(slot_2_index)
            except ValueError:
                raise EventParsingError(usage)
            if max(slot_1_index, slot_2_index) > len(gs.inventory):
                raise EventParsingError('Inventory slot needs to be between'
                                        f' 1 and {len(gs.inventory)}')
            slot_1 = gs.inventory[slot_1_index]
            slot_2 = gs.inventory[slot_2_index]
            gs.inventory[slot_1_index] = slot_2
            gs.inventory[slot_2_index] = slot_1
            text = (f'Switched {slot_1.item} (slot {slot_1_index})'
                    f' for {slot_2.item} (slot {slot_2_index})')
        case 'autosort':
            items = list(Item) + [None]
            gs.inventory.sort(key=lambda s: items.index(s.item))
            text = 'Autosorted inventory'
        case _:
            usage = 'Usage: inventory [use/get/buy/sell/switch/autosort]'
            raise EventParsingError(usage)
    return Comment(gs, text)
