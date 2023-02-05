from itertools import zip_longest

from .data.characters import CharacterState
from .data.constants import EquipmentType, Stat
from .data.items import InventorySlot
from .data.monsters import Monster, MonsterState
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


def get_status_chance_table(seed: int, amount: int) -> str:
    """Returns a table-formatted string of the status
    chance rng rolls for party members and monsters.
    """
    rng_tracker = FFXRNGTracker(seed)
    digits = len(str(amount))
    columns = (
        f'Roll [{"#" * digits}]', 'Tidus', 'Yuna', 'Auron', 'Kimahri', 'Wakka',
        'Lulu', 'Rikku', 'Aeons', 'Mon1', 'Mon2', 'Mon3', 'Mon4', 'Mon5',
        'Mon6', 'Mon7', 'Mon8',
        )
    header = '| ' + '| '.join(columns) + '|'
    spacer = '-' * len(header)
    data = spacer + '\n'
    data += header + '\n'
    data += spacer + '\n'
    for i in range(amount):
        data += f'| Roll [{i + 1:>{digits}}]'
        for j, title in zip(range(52, 68), columns[1:]):
            data += f'| {rng_tracker.advance_rng(j) % 101:>{len(title)}}'
        data += '|\n'
    data += spacer
    return data


def format_monster_data(monster: Monster) -> str:
    data = treeview(vars(monster))
    data = data.split('\n')
    wrap = 55
    string = ''
    for one, two in zip_longest(data[:wrap], data[wrap:], fillvalue=' '):
        if two:
            string += f'{one:40}|{two}\n'
        else:
            string += f'{one}\n'
    return string


def ctb_sorter(characters: list[CharacterState],
               monsters: list[MonsterState],
               ) -> str:
    ctbs: list[tuple[str, str]] = []

    for c in characters:
        sort_key = f'{c.ctb:03}0{256 - c.stats[Stat.AGILITY]:03}{c.index:02}'
        string = f'{c.character[:2]:2}[{c.ctb}]'
        ctbs.append((sort_key, string))

    for m in monsters:
        sort_key = f'{m.ctb:03}1{m.slot:02}{256 - m.stats[Stat.AGILITY]:03}'
        string = f'M{m.slot + 1}[{m.ctb}]'
        ctbs.append((sort_key, string))

    # sorting by icv, then by party, then by agility and index (for characters)
    # or index and agility (for monsters)
    ctbs.sort(key=lambda v: v[0])
    ctbs = [v[1] for v in ctbs]
    return ' '.join(ctbs)


def get_inventory_table(inventory: list[InventorySlot]) -> str:
    left = True
    left_padding = 0
    right_padding = 0
    for slot in inventory:
        padding = len(str(slot)) - 1
        if left:
            left_padding = max(left_padding, padding)
            left = False
        else:
            right_padding = max(right_padding, padding)
            left = True

    text = f'+-{"-" * left_padding}-+-{"-" * right_padding}-+\n'
    rows = []
    for slot_index in range(0, len(inventory), 2):
        row = '|'
        left_slot = inventory[slot_index]
        if left_slot.item:
            padding = left_padding - len(left_slot.item)
            row += f' {left_slot.item}{left_slot.quantity:{padding}} |'
        else:
            row += f' {"-":{left_padding}} |'
        right_slot = inventory[slot_index + 1]
        if right_slot.item:
            padding = right_padding - len(right_slot.item)
            row += f' {right_slot.item}{right_slot.quantity:{padding}} |'
        else:
            row += f' {"-":{right_padding}} |'
        rows.append(row)
    empty_row = f'| {"-":{left_padding}} | {"-":{right_padding}} |'
    while rows[-1] == empty_row:
        rows.pop()
    text += '\n'.join(rows)
    text += f'\n+-{"-" * left_padding}-+-{"-" * right_padding}-+'
    return text
