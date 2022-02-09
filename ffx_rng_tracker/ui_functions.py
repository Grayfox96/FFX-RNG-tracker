from itertools import product, zip_longest

from .data.actions import ACTIONS, YOJIMBO_ACTIONS
from .data.characters import CHARACTERS, Character
from .data.constants import EncounterCondition, EquipmentType, Stat
from .data.monsters import MONSTERS, Monster
from .data.zones import Zone
from .events.advance_rng import AdvanceRNG
from .events.change_party import ChangeParty
from .events.change_stat import ChangeStat
from .events.character_action import CharacterAction
from .events.comment import Comment
from .events.death import Death
from .events.encounter import (Encounter, MultizoneRandomEncounter,
                               RandomEncounter, SimulatedEncounter)
from .events.encounter_check import walk
from .events.escape import Escape
from .events.kill import Bribe, Kill
from .events.steal import Steal
from .events.yojimbo_turn import YojimboTurn
from .main import get_tracker
from .utils import treeview


def get_equipment_types(amount: int, columns: int = 2) -> str:
    """Returns a table formatted string with equipment types information."""
    rng_tracker = get_tracker()
    rng_tracker.reset()
    equipment_types = []
    for i in range(amount):
        rng_tracker.advance_rng(12)
        rng_weapon_or_armor = rng_tracker.advance_rng(12)
        rng_tracker.advance_rng(12)
        rng_tracker.advance_rng(12)
        if rng_weapon_or_armor & 1 == 0:
            equipment_type = EquipmentType.WEAPON
        else:
            equipment_type = EquipmentType.ARMOR
        equipment_types.append(equipment_type)
    rng_tracker.reset()

    spacer = ('-' * ((14 + len(str(amount))) * columns + 1)) + '\n'
    data = f'First {amount} equipment types\n{spacer}'
    for _ in range(columns):
        data += f'| [{"#" * len(str(amount))}] |   Type '
    data += f'|\n{spacer}'
    for i in range(amount // columns):
        for j in range(columns):
            j = j * (amount // columns)
            data += f'| [{i + j + 1:2}] | {equipment_types[i + j]:>6} '
        data += '|\n'
    data += spacer
    return data


def get_encounter_predictions(delta: int = 6) -> str:
    step_ranges = (
        (64, 64 + delta),
        (142, 142 + delta),
        (39, 39 + (delta // 2)),
    )
    zones = (
        Zone('Underwater Ruins', 30, 240),
        Zone('Besaid Lagoon', 30, 240),
        Zone('Besaid Road', 35, 280),
    )
    tracker = get_tracker()
    predictions = {z.name: {} for z in zones}
    total_occurrences = 0
    for steps_list in product(*[range(*s) for s in step_ranges]):
        total_occurrences += 1
        tracker.reset()
        for steps, zone in zip(steps_list, zones):
            n = sum([1 for e in walk(steps, zone) if e.encounter])
            predictions[zone.name][n] = predictions[zone.name].get(n, 0) + 1
    tracker.reset()
    for (zone, prediction), steps in zip(predictions.items(), step_ranges):
        for n_encs, occurrences in prediction.items():
            prediction[n_encs] = f'{occurrences * 100 / total_occurrences}%'
        new_key = f'{zone}, {steps[0]}-{steps[1]} steps'
        predictions[new_key] = predictions.pop(zone)
    return predictions


def parse_encounter(
        encounter_type: str = '', name: str = '', initiative: str = '',
        forced_condition: str = '', *_) -> Encounter:
    if encounter_type in ('set', 'set_optional'):
        encounter_type = Encounter
    elif encounter_type == 'random':
        encounter_type = RandomEncounter
    elif encounter_type == 'simulated':
        encounter_type = SimulatedEncounter
    elif encounter_type == 'multizone':
        encounter_type = MultizoneRandomEncounter
    initiative = initiative == 'true'
    condition = None
    if forced_condition:
        for ec in EncounterCondition:
            if ec.lower().startswith(forced_condition):
                condition = ec
    return encounter_type(name, initiative, condition)


def parse_steal(
        monster_name: str = '', successful_steals: str = '0',
        *_) -> Steal | Comment:
    usage = 'Usage: steal [monster_name] (successful steals)'
    if not monster_name:
        return Comment(usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError:
        return Comment(f'No monster named {monster_name!r}')
    try:
        successful_steals = int(successful_steals)
    except ValueError:
        return Comment(usage)
    return Steal(monster, successful_steals)


def parse_kill(
        monster_name: str = '', killer_name: str = '',
        overkill: str = '', *_) -> Kill | Comment:
    usage = 'Usage: (kill) [monster_name] [killer] (overkill/ok)'
    if not monster_name or not killer_name:
        return Comment(usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        return Comment(f'No monster named {error}')
    overkill = overkill in ('overkill', 'ok')
    killer = CHARACTERS.get(killer_name, Character('Other', 18))
    return Kill(monster, killer, overkill)


def parse_bribe(
        monster_name: str = '', user_name: str = '', *_) -> Bribe | Comment:
    usage = 'Usage: bribe [monster_name] [user]'
    if not monster_name or not user_name:
        return Comment(usage)
    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        return Comment(f'No monster named {error}')
    killer = CHARACTERS.get(user_name, Character('Other', 18))
    return Bribe(monster, killer)


def parse_death(character: str = '???', *_) -> Death:
    character = CHARACTERS.get(character, Character('Unknown', 18))
    return Death(character)


def parse_roll(
        rng_index: str = '', times: str = '1', *_) -> AdvanceRNG | Comment:
    usage = 'Usage: waste/advance/roll [rng#] [amount]'
    try:
        if rng_index.startswith('rng'):
            rng_index = int(rng_index[3:])
        else:
            rng_index = int(rng_index)
        times = int(times)
    except ValueError:
        return Comment(usage)
    if times > 100000:
        return Comment('Can\'t advance rng more than 100000 times.')
    if not (0 <= rng_index < 68):
        return Comment(f'Can\'t advance rng index {rng_index}')
    return AdvanceRNG(rng_index, times)


def parse_party_change(
        party_formation_string: str = '', *_) -> ChangeParty | Comment:
    usage = 'Usage: party [party members initials]'
    if not party_formation_string:
        return Comment(usage)
    party_formation = []
    characters = tuple(CHARACTERS.values())[:7]
    for character in characters:
        initial = character.name[0].lower()
        if initial in party_formation_string:
            party_formation.append(character)

    if party_formation == []:
        return Comment(usage)
    return ChangeParty(party_formation)


def parse_action(
        character_name: str = '', action_name: str = '',
        target_name: str = '', *_) -> CharacterAction | Escape | Comment:
    usage = 'Usage: [character] [action name] (target)'
    if not character_name or not action_name:
        return Comment(usage)

    if target_name.endswith('_c'):
        try:
            target = CHARACTERS[target_name[:-2]]
        except KeyError as error:
            return Comment(f'No character named {error}')
    elif target_name:
        try:
            target = MONSTERS[target_name]
        except KeyError:
            try:
                target = CHARACTERS[target_name]
            except KeyError as error:
                return Comment(f'No target named {error}')
    else:
        target = None

    try:
        character = CHARACTERS[character_name]
    except KeyError:
        return Comment(f'No character named {character_name}')

    if action_name == 'escape':
        if character.index > 6:
            return Comment(f'Character {character.name!r} can\'t '
                           'perform action \'Escape\'')
        return Escape(character)
    else:
        try:
            action = ACTIONS[action_name]
        except KeyError:
            return Comment(f'No action named {action_name!r}')
        if target is None and action.has_target:
            return Comment(f'Action {action.name!r} requires a target.')
        return CharacterAction(character, action, target)


def parse_stat_update(
        character_name: str = '', stat_name: str = '',
        amount: str = '', *_) -> ChangeStat | Comment:
    usage = 'Usage: stat [character] [stat] [(+/-) amount]'
    if not character_name or not stat_name or not amount:
        return Comment(usage)
    try:
        character = CHARACTERS[character_name]
    except KeyError as error:
        return Comment(f'No character named {error}')
    for stat in Stat:
        if str(stat).lower().replace(' ', '_') == stat_name:
            stat_value = character.stats[stat]
            break
    else:
        return Comment(f'No stat named {stat_name}')
    try:
        if amount.startswith('+'):
            stat_value += int(amount[1:])
        elif amount.startswith('-'):
            stat_value -= int(amount[1:])
        else:
            stat_value = int(amount)
    except ValueError:
        return Comment('Stat value should be an integer.')
    return ChangeStat(character, stat, stat_value)


def parse_yojimbo_action(
        action_name: str = '', monster_name: str = '',
        overdrive: str = '', *_) -> YojimboTurn | Comment:
    usage = 'Usage: [action] [monster] (overdrive)'
    if not action_name or not monster_name:
        return Comment(usage)
    try:
        attack = YOJIMBO_ACTIONS[action_name]
    except KeyError as error:
        return Comment(f'No action named {error}')

    try:
        monster = MONSTERS[monster_name]
    except KeyError as error:
        return Comment(f'No monster named {error}')

    overdrive = overdrive == 'overdrive'

    return YojimboTurn(attack, monster, overdrive)


def parse_compatibility_update(new_compatibility: str = '', *_) -> Comment:
    usage = 'Usage: compatibility [(+/-)amount]'
    rng_tracker = get_tracker()
    compatibility = rng_tracker.compatibility
    try:
        if new_compatibility.startswith('+'):
            compatibility += int(new_compatibility[1:])
        elif new_compatibility.startswith('-'):
            compatibility -= int(new_compatibility[1:])
        else:
            compatibility = int(new_compatibility)
    except ValueError:
        return Comment(usage)

    rng_tracker.compatibility = max(min(compatibility, 255), 0)
    return Comment(f'Compatibility changed to {rng_tracker.compatibility}')


def get_status_chance_string(amount: int = 50) -> str:
    """Returns a table-formatted string of the status
    chance rng rolls for party members and enemies.
    """
    rng_tracker = get_tracker()
    rng_tracker.reset()
    digits = len(str(amount))
    spacer = ('-' * (202 + digits)) + '\n'
    data = spacer
    data += (f'| Roll [{"#" * digits}]|      Tidus|       Yuna|      Auron'
             '|    Kimahri|      Wakka|       Lulu|      Rikku|      Aeons'
             '|    Enemy 1|    Enemy 2|    Enemy 3|    Enemy 4|    Enemy 5'
             '|    Enemy 6|    Enemy 7|    Enemy 8|\n')
    data += spacer
    for i in range(amount):
        data += f'| Roll [{i + 1:>{digits}}]'
        for j in range(52, 68):
            data += f'| {rng_tracker.advance_rng(j) % 101:>10}'
        data += '|\n'
    data += spacer
    rng_tracker.reset()
    return data


def format_monster_data(monster: Monster) -> str:
    data = treeview(vars(monster))
    data = data.split('\n')
    wrap = 54
    string = ''
    for one, two in zip_longest(data[:wrap], data[wrap:], fillvalue=' '):
        string += f'{one:40}|{two}\n'
    return string
