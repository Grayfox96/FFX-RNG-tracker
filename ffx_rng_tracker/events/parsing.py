from itertools import product

from ..data.actions import ACTIONS, YOJIMBO_ACTIONS
from ..data.characters import CHARACTERS, Character
from ..data.constants import EncounterCondition, Stat
from ..data.monsters import MONSTERS
from .advance_rng import AdvanceRNG
from .change_party import ChangeParty
from .change_stat import ChangeStat
from .character_action import CharacterAction
from .comment import Comment
from .death import Death
from .encounter import (Encounter, MultizoneRandomEncounter, RandomEncounter,
                        SimulatedEncounter)
from .escape import Escape
from .kill import Bribe, Kill
from .main import GameState
from .monster_action import MonsterAction
from .steal import Steal
from .yojimbo_turn import YojimboTurn


def parse_encounter(
        gs: GameState, type_: str = '', name: str = '', initiative: str = '',
        forced_condition: str = '', *_,) -> Encounter | Comment:
    match type_:
        case 'set' | 'set_optional':
            encounter_type = Encounter
        case 'random':
            encounter_type = RandomEncounter
        case 'simulated':
            encounter_type = SimulatedEncounter
        case 'multizone':
            encounter_type = MultizoneRandomEncounter
        case _:
            return Comment(gs, f'Invalid encounter type: {type_}')
    initiative = initiative == 'true'
    condition = None
    if forced_condition:
        for ec in EncounterCondition:
            if ec.lower().startswith(forced_condition):
                condition = ec
    return encounter_type(gs, name, initiative, condition)


def parse_steal(
        gs: GameState, monster_name: str = '', successful_steals: str = '0',
        *_) -> Steal | Comment:
    usage = 'Usage: steal [monster_name] (successful steals)'
    if not monster_name:
        return Comment(gs, usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError:
        return Comment(gs, f'No monster named {monster_name!r}')
    try:
        successful_steals = int(successful_steals)
    except ValueError:
        return Comment(gs, usage)
    return Steal(gs, monster, successful_steals)


def parse_kill(
        gs: GameState, monster_name: str = '', killer_name: str = '',
        overkill: str = '', *_) -> Kill | Comment:
    usage = 'Usage: (kill) [monster_name] [killer] (overkill/ok)'
    if not monster_name or not killer_name:
        return Comment(gs, usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        return Comment(gs, f'No monster named {error}')
    overkill = overkill in ('overkill', 'ok')
    killer = CHARACTERS.get(killer_name, Character('Other', 18))
    return Kill(gs, monster, killer, overkill)


def parse_bribe(
        gs: GameState, monster_name: str = '', user_name: str = '',
        *_) -> Bribe | Comment:
    usage = 'Usage: bribe [monster_name] [user]'
    if not monster_name or not user_name:
        return Comment(gs, usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        return Comment(gs, f'No monster named {error}')
    killer = CHARACTERS.get(user_name, Character('Other', 18))
    return Bribe(gs, monster, killer)


def parse_death(gs: GameState, character: str = '???', *_) -> Death:
    character = CHARACTERS.get(character, Character('Unknown', 18))
    return Death(gs, character)


def parse_roll(
        gs: GameState, rng_index: str = '', times: str = '1',
        *_) -> AdvanceRNG | Comment:
    usage = 'Usage: waste/advance/roll [rng#] [amount]'
    try:
        if rng_index.startswith('rng'):
            rng_index = int(rng_index[3:])
        else:
            rng_index = int(rng_index)
        times = int(times)
    except ValueError:
        return Comment(gs, usage)
    if times > 100000:
        return Comment(gs, 'Can\'t advance rng more than 100000 times.')
    if not (0 <= rng_index < 68):
        return Comment(gs, f'Can\'t advance rng index {rng_index}')
    return AdvanceRNG(gs, rng_index, times)


def parse_party_change(
        gs: GameState, party_formation_string: str = '',
        *_) -> ChangeParty | Comment:
    usage = 'Usage: party [party members initials]'
    if not party_formation_string:
        return Comment(gs, usage)
    party_formation = []
    characters = tuple(CHARACTERS)[:7]
    for c, character in product(party_formation_string, characters):
        if c == CHARACTERS[character].name[0].lower():
            party_formation.append(character)
    # remove duplicates and keep order
    party_formation = list(dict.fromkeys(party_formation))
    party_formation = [CHARACTERS[c] for c in party_formation]

    if not party_formation:
        return Comment(gs, usage)
    return ChangeParty(gs, party_formation)


def parse_action(
        gs: GameState, character_name: str = '', action_name: str = '',
        target_name: str = '', *_) -> CharacterAction | Escape | Comment:
    usage = 'Usage: [character] [action name] (target)'
    if not character_name or not action_name:
        return Comment(gs, usage)

    if target_name.endswith('_c'):
        try:
            target = CHARACTERS[target_name[:-2]]
        except KeyError as error:
            return Comment(gs, f'No character named {error}')
    elif target_name:
        try:
            target = MONSTERS[target_name]
        except KeyError:
            try:
                target = CHARACTERS[target_name]
            except KeyError as error:
                return Comment(gs, f'No target named {error}')
    else:
        target = None

    try:
        character = CHARACTERS[character_name]
    except KeyError:
        return Comment(gs, f'No character named {character_name}')

    if action_name == 'escape':
        if character.index > 6:
            return Comment(
                gs,
                f'Character {character.name!r} can\'t perform action "Escape"'
            )
        return Escape(gs, character)
    else:
        try:
            action = ACTIONS[action_name]
        except KeyError:
            return Comment(gs, f'No action named {action_name!r}')
        if target is None and action.has_target:
            return Comment(gs, f'Action {action.name!r} requires a target.')
        return CharacterAction(gs, character, action, target)


def parse_stat_update(
        gs: GameState, character_name: str = '', stat_name: str = '',
        amount: str = '', *_) -> ChangeStat | Comment:
    usage = 'Usage: stat [character] [stat] [(+/-) amount]'
    if not character_name or not stat_name or not amount:
        return Comment(gs, usage)
    try:
        character = CHARACTERS[character_name]
    except KeyError as error:
        return Comment(gs, f'No character named {error}')
    for stat in Stat:
        if str(stat).lower().replace(' ', '_') == stat_name:
            stat_value = character.stats[stat]
            break
    else:
        return Comment(gs, f'No stat named {stat_name}')
    try:
        if amount.startswith('+'):
            stat_value += int(amount[1:])
        elif amount.startswith('-'):
            stat_value -= int(amount[1:])
        else:
            stat_value = int(amount)
    except ValueError:
        return Comment(gs, 'Stat value should be an integer.')
    return ChangeStat(gs, character, stat, stat_value)


def parse_yojimbo_action(
        gs: GameState, action_name: str = '', monster_name: str = '',
        overdrive: str = '', *_) -> YojimboTurn | Comment:
    usage = 'Usage: [action] [monster] (overdrive)'
    if not action_name or not monster_name:
        return Comment(gs, usage)
    try:
        attack = YOJIMBO_ACTIONS[action_name]
    except KeyError as error:
        return Comment(gs, f'No action named {error}')

    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        return Comment(gs, f'No monster named {error}')

    overdrive = overdrive == 'overdrive'

    return YojimboTurn(gs, attack, monster, overdrive)


def parse_compatibility_update(
        gs: GameState, compatibility: str = '', *_) -> Comment:
    usage = 'Usage: compatibility [(+/-)amount]'
    try:
        if compatibility.startswith('+'):
            gs.compatibility += int(compatibility[1:])
        elif compatibility.startswith('-'):
            gs.compatibility -= int(compatibility[1:])
        else:
            gs.compatibility = int(compatibility)
    except ValueError:
        return Comment(gs, usage)

    return Comment(gs, f'Compatibility changed to {gs.compatibility}')


def parse_monster_action(
        gs: GameState, monster_name: str = '', *_) -> MonsterAction | Comment:
    usage = 'Usage: [monster_name]'

    if monster_name not in MONSTERS:
        return Comment(gs, usage)
    return MonsterAction(gs, MONSTERS[monster_name], ACTIONS['attack'], 0)
