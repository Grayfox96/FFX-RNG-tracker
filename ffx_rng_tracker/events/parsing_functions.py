from typing import Callable

from ..data.actions import ACTIONS, YOJIMBO_ACTIONS
from ..data.constants import (Autoability, Character, EquipmentType, Stat,
                              TargetType)
from ..data.encounter_formations import BOSSES, SIMULATIONS, ZONES
from ..data.equipment import Equipment
from ..data.monsters import MONSTERS, MonsterState
from ..errors import EventParsingError
from ..gamestate import GameState
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
from .end_encounter import EndEncounter
from .escape import Escape
from .heal_party import Heal
from .kill import Bribe, Kill
from .main import Event
from .monster_action import MonsterAction
from .steal import Steal
from .yojimbo_turn import YojimboTurn

ParsingFunction = (Callable[[GameState, str], Event]
                   | Callable[[GameState, str, str], Event]
                   | Callable[[GameState, str, str, str], Event]
                   | Callable[..., Event]
                   )


def parse_encounter(gs: GameState,
                    name: str = '',
                    *zones: str,
                    ) -> Encounter:
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


def parse_steal(gs: GameState,
                monster_name: str = '',
                successful_steals: str = '0',
                *_,
                ) -> Steal:
    usage = 'Usage: steal [monster_name] (successful steals)'
    if not monster_name:
        raise EventParsingError(usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError:
        raise EventParsingError(f'No monster named "{monster_name}"')
    try:
        successful_steals = int(successful_steals)
    except ValueError:
        raise EventParsingError(usage)
    return Steal(gs, monster, successful_steals)


def parse_kill(gs: GameState,
               monster_name: str = '',
               killer_name: str = '',
               overkill: str = '',
               *_,
               ) -> Kill:
    usage = 'Usage: (kill) [monster_name] [killer] (overkill/ok)'
    if not monster_name or not killer_name:
        raise EventParsingError(usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        raise EventParsingError(f'No monster named {error}')
    overkill = overkill in ('overkill', 'ok')
    try:
        killer = search_stringenum(Character, killer_name)
    except ValueError:
        raise EventParsingError(f'No character called {killer_name}')
    return Kill(gs, monster, killer, overkill)


def parse_bribe(gs: GameState,
                monster_name: str = '',
                user_name: str = '',
                *_,
                ) -> Bribe:
    usage = 'Usage: bribe [monster_name] [user]'
    if not monster_name or not user_name:
        raise EventParsingError(usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        raise EventParsingError(f'No monster named {error}')
    try:
        user = search_stringenum(Character, user_name)
    except ValueError:
        raise EventParsingError(f'No character called {user_name}')
    return Bribe(gs, monster, user)


def parse_death(gs: GameState, character_name: str = '', *_) -> Death:
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
    if times > 100000:
        raise EventParsingError('Can\'t advance rng more than 100000 times.')
    if not (0 <= rng_index < 68):
        raise EventParsingError(f'Can\'t advance rng index {rng_index}')
    return AdvanceRNG(gs, rng_index, times)


def parse_party_change(gs: GameState,
                       party_formation_string: str = '',
                       *_,
                       ) -> ChangeParty:
    usage = 'Usage: party [party members initials]'
    if not party_formation_string:
        raise EventParsingError(usage)
    party_formation = []
    for character in tuple(Character)[:7]:
        initial = stringify(character)[0]
        for letter in party_formation_string:
            if initial == letter:
                party_formation.append(character)
                break

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
        for aeon in tuple(Character)[7:]:
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

    try:
        character = search_stringenum(Character, character_name)
    except ValueError:
        raise EventParsingError(f'No character named {character_name}')

    character = gs.characters[character]

    if action_name == 'escape':
        return Escape(gs, character)
    try:
        action = ACTIONS[action_name]
    except KeyError:
        raise EventParsingError(f'No action named "{action_name}"')

    if action.target is TargetType.SELF:
        target = character
    elif target_name.startswith('m') and target_name[1:].isdigit():
        target_index = int(target_name[1:]) - 1
        try:
            target = gs.monster_party[target_index]
        except IndexError:
            raise EventParsingError(
                f'Monster slot must be between 1 and {len(gs.monster_party)}')
    elif target_name.endswith('_c'):
        try:
            target = search_stringenum(Character, target_name[:-2])
        except ValueError:
            raise EventParsingError(f'No target named {target_name}')
        target = gs.characters[target]
    elif target_name:
        try:
            target = MonsterState(MONSTERS[target_name])
        except KeyError:
            try:
                target = search_stringenum(Character, target_name)
            except ValueError:
                raise EventParsingError(f'No target named {target_name}')
            target = gs.characters[target]
    else:
        target = None

    if target is None:
        raise EventParsingError(f'Action "{action}" requires a target.')
    try:
        time_remaining = int(time_remaining)
    except ValueError:
        time_remaining = 0
    return CharacterAction(gs, character, action, target, time_remaining)


def parse_stat_update(gs: GameState,
                      character_name: str = '',
                      stat_name: str = '',
                      amount: str = '',
                      *_,
                      ) -> ChangeStat:
    usage = 'Usage: stat [character] [stat] [(+/-) amount]'
    if not character_name or not stat_name or not amount:
        raise EventParsingError(usage)
    try:
        character = search_stringenum(Character, character_name)
    except ValueError:
        raise EventParsingError(f'No character named {character_name}')
    character = gs.characters[character]
    try:
        stat = search_stringenum(Stat, stat_name)
    except ValueError:
        raise EventParsingError(f'No stat named {stat_name}')
    stat_value = character.stats[stat]
    try:
        if amount.startswith('+'):
            stat_value += int(amount[1:])
        elif amount.startswith('-'):
            stat_value -= int(amount[1:])
        else:
            stat_value = int(amount)
    except ValueError:
        raise EventParsingError('Stat value should be an integer.')
    return ChangeStat(gs, character, stat, stat_value)


def parse_yojimbo_action(gs: GameState,
                         action_name: str = '',
                         monster_name: str = '',
                         overdrive: str = '',
                         *_,
                         ) -> YojimboTurn:
    usage = 'Usage: [action] [monster] (overdrive)'
    if not action_name or not monster_name:
        raise EventParsingError(usage)
    try:
        attack = YOJIMBO_ACTIONS[action_name]
    except KeyError as error:
        raise EventParsingError(f'No action named {error}')

    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        raise EventParsingError(f'No monster named {error}')

    overdrive = overdrive == 'overdrive'

    return YojimboTurn(gs, attack, monster, overdrive)


def parse_compatibility_update(gs: GameState,
                               compatibility: str = '',
                               *_,
                               ) -> Comment:
    usage = 'Usage: compatibility [(+/-)amount]'
    try:
        if compatibility.startswith('+'):
            gs.compatibility += int(compatibility[1:])
        elif compatibility.startswith('-'):
            gs.compatibility -= int(compatibility[1:])
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

    if monster_name.isdecimal():
        slot = int(monster_name)
        if not (1 <= slot <= 8):
            raise EventParsingError('Slot must be between 1 and 8')
        slot -= 1
        try:
            monster = gs.monster_party[slot]
        except IndexError:
            raise EventParsingError(
                f'Slot must be between 1 and {len(gs.monster_party)}')
    else:
        try:
            monster = MONSTERS[monster_name]
        except KeyError:
            raise EventParsingError(usage)
        monster = MonsterState(monster)
    try:
        action = monster.monster.actions[action_name]
    except KeyError:
        action_names = ', '.join(str(a) for a in monster.monster.actions)
        raise EventParsingError(f'Available actions for {monster}: '
                                f'{action_names}')
    return MonsterAction(gs, monster, action)


def parse_equipment_change(gs: GameState,
                           character_name: str = '',
                           equipment_type_name: str = '',
                           slots: str = '',
                           *ability_names: str,
                           ) -> ChangeEquipment:
    usage = 'Usage: equip [character] [equip_type] [slots] (abilities)'
    if not all((character_name, equipment_type_name, slots)):
        raise EventParsingError(usage)
    try:
        character = search_stringenum(Character, character_name)
    except ValueError:
        raise EventParsingError(f'No character named {character_name}')
    try:
        equipment_type = search_stringenum(EquipmentType, equipment_type_name)
    except ValueError:
        raise EventParsingError('Equipment type can be weapon or armor')
    try:
        slots = int(slots)
    except ValueError:
        raise EventParsingError('Slots must be a number between 0 and 4')
    if not (0 <= slots <= 4):
        raise EventParsingError('Slots must be a number between 0 and 4')
    abilities = []
    for ability_name in ability_names:
        if len(abilities) >= 4:
            break
        try:
            ability = search_stringenum(Autoability, ability_name)
        except ValueError:
            raise EventParsingError(f'No autoability called {ability_name}')
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
    return ChangeEquipment(gs, equipment)


def parse_end_encounter(gs: GameState, *_) -> EndEncounter:
    return EndEncounter(gs)


def parse_heal(gs: GameState,
               character_name: str = '',
               amount: str = '99999',
               *_) -> Heal:
    characters = []
    if character_name:
        try:
            character = search_stringenum(Character, character_name)
        except ValueError:
            raise EventParsingError(f'No character called {character_name}')
        characters.append(character)
    else:
        characters.extend([c for c in Character][:-1])
    try:
        amount = int(amount)
    except ValueError:
        amount = 99999

    return Heal(gs, characters, amount)
