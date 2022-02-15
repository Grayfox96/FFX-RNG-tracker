from itertools import product, zip_longest

from .data.constants import EquipmentType
from .data.monsters import Monster
from .data.zones import Zone
from .events.encounter_check import walk
from .events.main import GameState
from .tracker import FFXRNGTracker
from .utils import treeview


def get_equipment_types(seed: int, amount: int, columns: int = 2) -> str:
    """Returns a table formatted string with equipment types information."""
    rng_tracker = FFXRNGTracker(seed)
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


def get_encounter_predictions(seed: int, delta: int = 6) -> str:
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
    gs = GameState(seed)
    predictions = {z.name: {} for z in zones}
    total_occurrences = 0
    for steps_list in product(*[range(*s) for s in step_ranges]):
        total_occurrences += 1
        gs.reset()
        for steps, zone in zip(steps_list, zones):
            n = sum([1 for e in walk(gs, steps, zone) if e.encounter])
            predictions[zone.name][n] = predictions[zone.name].get(n, 0) + 1
    for (zone, prediction), steps in zip(predictions.items(), step_ranges):
        for n_encs, occurrences in prediction.items():
            prediction[n_encs] = f'{occurrences * 100 / total_occurrences}%'
        new_key = f'{zone}, {steps[0]}-{steps[1]} steps'
        predictions[new_key] = predictions.pop(zone)
    return predictions


def get_status_chance_string(seed: int, amount: int = 50) -> str:
    """Returns a table-formatted string of the status
    chance rng rolls for party members and enemies.
    """
    rng_tracker = FFXRNGTracker(seed)
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
    return data


def format_monster_data(monster: Monster) -> str:
    data = treeview(vars(monster))
    data = data.split('\n')
    wrap = 54
    string = ''
    for one, two in zip_longest(data[:wrap], data[wrap:], fillvalue=' '):
        string += f'{one:40}|{two}\n'
    return string
