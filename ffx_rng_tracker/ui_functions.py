from itertools import batched, chain

from .data.actor import CharacterActor, MonsterActor
from .data.constants import Character, EquipmentType, KillType, Stat
from .data.monsters import Monster
from .tracker import FFXRNGTracker


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
    data = f'First {amount} Equipment Types\n{spacer}'
    for _ in range(columns):
        data += f'| [{'#' * len(str(amount))}] |   Type '
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
        f'Roll [{'#' * digits}]', 'Tidus', 'Yuna', 'Auron', 'Kimahri', 'Wakka',
        'Lulu', 'Rikku', 'Aeons', 'Mon1', 'Mon2', 'Mon3', 'Mon4', 'Mon5',
        'Mon6', 'Mon7', 'Mon8',
        )
    header = '| ' + '| '.join(columns) + '|'
    spacer = '-' * len(header)
    data = (f'First {amount} Status Rolls for each Character/Monster Slot\n'
            f'{spacer}\n{header}\n{spacer}\n')
    for i in range(amount):
        data += f'| Roll [{i + 1:>{digits}}]'
        for j, title in zip(range(52, 68), columns[1:]):
            data += f'| {rng_tracker.advance_rng(j) % 101:>{len(title)}}'
        data += '|\n'
    data += spacer
    return data


def dict_to_table(dictionary: dict,
                  rows: int = 1,
                  indentation: int = 1,
                  ) -> str:
    rows = max(1, rows)
    row_len = len(dictionary) // rows
    while (rows * row_len) < len(dictionary):
        rows += 1

    cells: list[str] = []
    paddings: dict[int, int] = {}
    for i, (k, v) in enumerate(dictionary.items()):
        column = i % row_len
        match v:
            case set() | list():
                v = ', '.join(str(i) for i in v)
            case dict():
                v = ', '.join([f'{k} {v}' for k, v in v.items()])
            case _:
                v = str(v)
        if not v:
            v = 'None'
        k = str(k)
        cell = f'{k}: {v}'
        cells.append(cell)
        paddings[column] = max(len(cell), paddings.get(column, 0))
    cells.extend(['' for _ in range((row_len * rows) - len(cells))])

    table_lines = ['+'] + ['|', '+'] * rows
    if indentation > 0:
        for i, line in enumerate(table_lines):
            table_lines[i] = (' ' * indentation * 4) + line

    for i, cell in enumerate(cells):
        row, column = divmod(i, row_len)
        row_offset = (rows - row - 1) * 2
        padding = paddings[column]
        spacer = f'-{'-' * padding}-+'
        if row == 0:
            table_lines[-3 - row_offset] += spacer
        table_lines[-2 - row_offset] += f' {cell:{padding}} |'
        table_lines[-1 - row_offset] += spacer
    table_lines[0] = table_lines[0].replace('-', '=')
    table_lines[-1] = table_lines[-1].replace('-', '=')
    return '\n'.join(table_lines)


def format_monster_data(monster: Monster) -> str:
    data: list[str] = []
    data.append(f'Index: {monster.index}')
    data.append(f'Name: {monster.name}')
    data.append(f'Zones: {', '.join(monster.zones)}')
    data.append(f'Stats:\n{dict_to_table(monster.stats)}')
    data.append(f'Elements:\n{dict_to_table(monster.elemental_affinities)}')
    data.append(f'Statuses:\n{dict_to_table(monster.status_resistances, 8)}')
    data.append('Auto-Statuses: ')
    if monster.auto_statuses:
        data[-1] += ', '.join(sorted(monster.auto_statuses))
    else:
        data[-1] += 'None'
    immunities = {
        'Percentage Damage': monster.immune_to_percentage_damage,
        'Life': monster.immune_to_life,
        'Sensor': monster.immune_to_sensor,
        'Scan': monster.immune_to_scan,
        'Physical Damage': monster.immune_to_physical_damage,
        'Magical Damage': monster.immune_to_magical_damage,
        'Damage': monster.immune_to_damage,
        'Delay': monster.immune_to_delay,
        'Slice': monster.immune_to_slice,
        'Bribe': monster.immune_to_bribe,
    }
    data.append(f'Immunities:\n{dict_to_table(immunities, 2)}')
    misc_info = {
        'Overkill threshold': monster.overkill_threshold,
        'Gil': monster.gil,
        'AP': monster.ap[KillType.NORMAL],
        'AP (Overkill)': monster.ap[KillType.OVERKILL],
        'Armored': monster.armored,
        'Poison tick damage': monster.poison_tick_damage,
        'Doom turns': monster.doom_turns,
        'Zanmato Lv': monster.zanmato_level,
    }
    data.append(f'Misc:\n{dict_to_table(misc_info, 2)}')

    items: list[str] = []
    for item in chain(monster.item_1.items.values(),
                      monster.item_2.items.values(),
                      monster.steal.items.values(),
                      ):
        if item is None:
            items.append('  None  ')
            continue
        items.append(f' {item.item} x{item.quantity} ')
    p = [len(i) for i in items[:8]]
    spacer = f'+{'+'.join(['-' * padding for padding in p])}+'
    data.append('Items:')
    data.append(f'+={'==+=='.join(['=' * sum(b) for b in batched(p, 4)])}=+')
    data.append(f'| {f'Item 1 ({monster.item_1.drop_chance}/255)':^{sum(p[:4])}}  '
                f'| {f'Item 2 ({monster.item_2.drop_chance}/255)':^{sum(p[4:])}}  |')
    data.append(f'+{'+'.join(['-' * (sum(b) + 1) for b in batched(p, 2)])}+')
    data.append(f'|{f'Normal':^{sum(p[:2]) + 1}}'
                f'|{f'Overkill':^{sum(p[2:4]) + 1}}'
                f'|{f'Normal':^{sum(p[4:6]) + 1}}'
                f'|{f'Overkill':^{sum(p[6:]) + 1}}|')
    data.append(f'+{'+'.join(['-' * (sum(b) + 1) for b in batched(p, 2)])}+')
    data.append(f'|{'|'.join(
        [f'{'Common':^{b[0]}}|{'Rare':^{b[1]}}' for b in batched(p, 2)])}|')
    data.append(spacer)
    data.append(f'|{'|'.join(items[:8])}|')
    data.append(spacer.replace('-', '='))

    items = items[8:]
    p = [len(i) for i in items]
    spacer = f'+{'+'.join(['-' * padding for padding in p])}+'
    data.append(f'+={'=' * sum(p)}+')
    data.append(f'|{f'Steal ({monster.steal.base_chance}/255)':^{sum(p) + 1}}|')
    data.append(spacer)
    data.append(f'|{'Common':^{p[0]}}|{'Rare':^{p[1]}}|')
    data.append(spacer)
    data.append(f'|{'|'.join(items)}|')
    data.append(spacer.replace('-', '='))

    item = f' {monster.bribe.item} ({monster.bribe.max_cost} Gil) '
    padding = len(item)
    spacer = f' +{'=' * padding}+'
    data[-5] += spacer
    data[-4] += f' |{'Bribe':^{padding}}|'
    data[-3] += spacer.replace('=', '-')
    data[-2] += f' |{item}|'
    data[-1] += spacer
    for i in range(-16, 0, 1):
        data[i] = f'    {data[i]}'

    equipment = {
        'Drop Chance': f'{monster.equipment.drop_chance}/255',
        'Bonus Critical Chance': monster.equipment.bonus_critical_chance,
        'Base Weapon Damage': monster.equipment.base_weapon_damage,
        'Added to Inventory': monster.equipment.added_to_inventory,
        'Slots Modifier': monster.equipment.slots_modifier,
        'Slots': monster.equipment.slots_range,
        'Ability Rolls Modifier': monster.equipment.max_ability_rolls_modifier,
        'Ability Rolls': monster.equipment.max_ability_rolls_range,
    }
    data.append(f'Equipment:\n{dict_to_table(equipment, 2)}')
    paddings: list[int] = [0] * 8
    ability_lists: list[list[str]] = []
    for equipment_type, characters in monster.equipment.ability_lists.items():
        for character, autoabilities in characters.items():
            aabs = []
            for i, autoability in enumerate(autoabilities):
                aab = str(autoability)
                aabs.append(aab)
                paddings[i] = max(len(aab), paddings[i])
            if character is Character.KIMAHRI:
                et = equipment_type
            else:
                et = ''
            data.append(f'| {et:6} | {character:7} | ')
            ability_lists.append(aabs)
    for row_offset, ability_list in enumerate(ability_lists):
        ability_list = [f'{aab:{p}}' for aab, p in zip(ability_list, paddings)]
        data[-14 + row_offset] += f'{' | '.join(ability_list)} |'
    paddings.insert(0, 6)
    paddings.insert(1, 7)
    spacer = f'+={'=+='.join(['=' * padding for padding in paddings])}=+'
    data.insert(-14, '    Auto-abilities:')
    data.insert(-14, spacer)
    data.insert(-7, spacer.replace('=', '-'))
    data.append(spacer)
    for i in range(-17, 0, 1):
        data[i] = f'{' ' * 8}{data[i]}'

    data.append('Actions:')
    data.append('    forced_action:')
    data.append(dict_to_table(vars(monster.forced_action), 12, 2))
    for name, action in monster.actions.items():
        data.append(f'    {name}:')
        data.append(dict_to_table(vars(action), 12, 2))
    return '\n'.join(data)


def ctb_sorter(characters: list[CharacterActor],
               monsters: list[MonsterActor],
               ) -> str:
    ctbs: list[tuple[str, str]] = []

    for c in characters:
        sort_key = f'{c.ctb:03}0{256 - c.stats[Stat.AGILITY]:03}{c.index:02}'
        string = f'{c.character[:2]:2}[{c.ctb}]'
        ctbs.append((sort_key, string))

    for m in monsters:
        sort_key = f'{m.ctb:03}1{m.index:02}{256 - m.stats[Stat.AGILITY]:03}'
        string = f'M{m.index + 1}[{m.ctb}]'
        ctbs.append((sort_key, string))

    # sorting by icv, then by party, then by agility and index (for characters)
    # or index and agility (for monsters)
    ctbs.sort(key=lambda v: v[0])
    ctbs = [v[1] for v in ctbs]
    return ' '.join(ctbs)
