from typing import Callable

from ..data.actions import ACTIONS, YOJIMBO_ACTIONS
from ..data.characters import s_lv_to_total_ap
from ..data.constants import (SHORT_STATS_NAMES, Autoability, Character,
                              EquipmentType, Item, KillType, MonsterSlot, Stat,
                              StringEnum, TargetType)
from ..data.encounter_formations import BOSSES, SIMULATIONS, ZONES
from ..data.equipment import Equipment
from ..data.items import ITEM_PRICES, ITEMS
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
    return equipment


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
    if not name:
        raise EventParsingError
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
    killer = parse_enum_member(killer_name, Character, 'character')
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
    user = parse_enum_member(user_name, Character, 'character')
    ap_characters = parse_party_members_initials(ap_characters_string)
    return Bribe(gs, monster, user, ap_characters)


def parse_death(gs: GameState, character_name: str = 'unknown', *_) -> Death:
    try:
        character = search_stringenum(Character, character_name)
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
        raise EventParsingError('Can\'t advance rng more than 100000 times.')
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


def parse_summon(gs: GameState,
                 aeon_name: str = '',
                 *_,
                 ) -> ChangeParty:
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
                 time_remaining: str = '0',
                 *_,
                 ) -> CharacterAction | Escape:
    if not character_name or not action_name:
        raise EventParsingError
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
    if not target_name:
        raise EventParsingError
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
            raise EventParsingError('amount must be an integer.')
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
        raise EventParsingError('amount must be an integer.')
    return ChangeStat(gs, target, stat, stat_value)


def parse_yojimbo_action(gs: GameState,
                         action_name: str = '',
                         monster_name: str = '',
                         overdrive: str = '',
                         *_,
                         ) -> YojimboTurn:
    if not action_name or not monster_name:
        raise EventParsingError
    action = parse_dict_key(action_name, YOJIMBO_ACTIONS, 'Yojimbo action')
    monster = parse_dict_key(monster_name, get_monsters_dict(), 'monster')
    overdrive = overdrive == 'overdrive'
    return YojimboTurn(gs, action, monster, overdrive)


def parse_compatibility_update(gs: GameState,
                               compatibility: str = '',
                               *_,
                               ) -> Comment:
    try:
        if compatibility.startswith(('+', '-')):
            gs.compatibility += int(compatibility)
        else:
            gs.compatibility = int(compatibility)
    except ValueError:
        raise EventParsingError
    return Comment(gs, f'Compatibility changed to {gs.compatibility}')


def parse_monster_action(gs: GameState,
                         monster_name: str = '',
                         action_name: str = '',
                         *_,
                         ) -> MonsterAction:
    if not monster_name:
        raise EventParsingError

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
        state = gs.characters[character]
        if amount:
            state.ap += amount
            added_ap = f' (added {amount} AP)'
        else:
            added_ap = ''
        next_s_lv_ap = (
            s_lv_to_total_ap(state.s_lv + 1, state.defaults.starting_s_lv)
            - state.ap
            )
        lines.append(f'{state.character}: {state.s_lv} S. Lv '
                     f'({state.ap} AP Total, {next_s_lv_ap} for next level)'
                     f'{added_ap}')
    return Comment(gs, '\n'.join(lines))


def parse_character_status(gs: GameState,
                           character_name: str = '',
                           *_) -> Comment:
    if not character_name:
        raise EventParsingError
    char = parse_enum_member(character_name, Character, 'character')
    char = gs.characters[char]
    text = f'{char}: hp {char.current_hp}, statuses {char.statuses}'
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
                text = get_inventory_table(gs.inventory)
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
            usage = f'Usage: inventory {command} gil [amount]'
            raise EventParsingError(usage)
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
                text = f'Added {item} x{amount} to inventory'
            elif command == 'buy':
                gil = ITEM_PRICES[item] * amount
                if gil > gs.gil:
                    raise EventParsingError('Not enough gil '
                                            f'(need {gil - gs.gil} more)')
                gs.gil -= gil
                text = f'Bought {item} x{amount} for {gil} gil'
            else:
                items = [s.item for s in gs.inventory]
                if item not in items:
                    raise EventParsingError(f'{item} is not in the inventory')
                slot = gs.inventory[items.index(item)]
                if amount > slot.quantity:
                    raise EventParsingError(f'Not enough {item} to {command}')
                if command == 'use':
                    text = f'Used {item} x{amount}'
                else:
                    gil = max(1, (ITEM_PRICES[item] // 4)) * amount
                    gs.gil += gil
                    text = f'Sold {item} x{amount} for {gil} gil'
                amount = amount * -1
            gs.add_to_inventory(item, amount)
        case ('get' | 'buy' | 'use' | 'sell', *_):
            usage = f'Usage: inventory {command} [item] [amount]'
            raise EventParsingError(usage)
        case ('switch', slot_1_index, slot_2_index, *_):
            try:
                slot_1_index = int(slot_1_index) - 1
                slot_2_index = int(slot_2_index) - 1
            except ValueError:
                raise EventParsingError('Inventory slot needs to be an integer')
            if (max(slot_1_index, slot_2_index) >= len(gs.inventory)
                    or min(slot_1_index, slot_2_index) < 0):
                raise EventParsingError('Inventory slot needs to be between'
                                        f' 1 and {len(gs.inventory)}')
            slot_1 = gs.inventory[slot_1_index]
            slot_2 = gs.inventory[slot_2_index]
            gs.inventory[slot_1_index] = slot_2
            gs.inventory[slot_2_index] = slot_1
            text = (f'Switched {slot_1.item} (slot {slot_1_index + 1})'
                    f' for {slot_2.item} (slot {slot_2_index + 1})')
        case ('switch', *_):
            usage = 'Usage: inventory switch [slot 1] [slot 2]'
            raise EventParsingError(usage)
        case ('autosort', *_):
            # TODO
            # autosort order is not by index
            items = list(ITEMS) + [None]
            gs.inventory.sort(key=lambda s: items.index(s.item))
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
        'encounters_count [total/random/zone] [(+/-)amount]',
        ],
    parse_steal: [
        'steal [monster_name] (successful steals)',
        ],
    parse_kill: [
        'kill [monster_name] [killer] (characters initials) (overkill/ok)',
    ],
    parse_bribe: [
        'bribe [monster_name] [user] (characters initials)',
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
        'action [character] [action] (target) (time remaining)',
    ],
    parse_stat_update: [
        'stat [character/monster slot] (stat) [(+/-)amount]',
    ],
    parse_yojimbo_action: [
        'yojimboturn [action] [monster] (overdrive)',
    ],
    parse_compatibility_update: [
        'compatibility ((+/-)amount)',
    ],
    parse_monster_action: [
        'monsteraction [monster slot/name] [action]',
    ],
    parse_equipment_change: [
        'equip [equip_type] [character] [slots] (abilities)',
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
    parse_character_status: [
        'status [character]',
    ],
    parse_monster_spawn: [
        'spawn [monster_name] [slot] (forced ctb)',
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
