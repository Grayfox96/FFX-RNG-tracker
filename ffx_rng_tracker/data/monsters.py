import json
from copy import deepcopy
from dataclasses import dataclass, field
from itertools import chain, count
from math import sqrt

from ..configs import Configs
from ..utils import add_bytes, open_cp1252, stringify
from .actions import ACTIONS, ACTIONS_FILES_BY_ID, Action
from .autoabilities import AUTOABILITIES
from .constants import (Autoability, Character, Element, ElementalAffinity,
                        EquipmentType, GameVersion, KillType, MonsterSlot,
                        Rarity, Stat, Status, TargetType)
from .file_functions import get_resource_path
from .items import ITEMS, ItemDrop
from .text_characters import bytes_to_string


@dataclass
class ItemDropInfo:
    drop_chance: int
    items: dict[tuple[KillType, Rarity], ItemDrop | None] = field(
        default_factory=dict)

    def __post_init__(self) -> None:
        self.items[KillType.NORMAL, Rarity.COMMON] = None
        self.items[KillType.NORMAL, Rarity.RARE] = None
        self.items[KillType.OVERKILL, Rarity.COMMON] = None
        self.items[KillType.OVERKILL, Rarity.RARE] = None


@dataclass
class ItemStealInfo:
    base_chance: int
    items: dict[Rarity, ItemDrop | None] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.items[Rarity.COMMON] = None
        self.items[Rarity.RARE] = None


@dataclass
class ItemBribeInfo:
    monster_hp: int
    item: ItemDrop | None = None

    @property
    def max_cost(self) -> int:
        return self.monster_hp * 25

    def get_chance(self, gil: int) -> float:
        chance = ((gil * 64 // (5 * self.monster_hp)) - 64) / 256
        return max(0.0, chance)

    def expected_items_range(self, gil: int) -> tuple[float, float]:
        item_quantity_base = sqrt(self.get_chance(gil))
        item_quantity = item_quantity_base * self.item.quantity
        item_quantity_min = item_quantity * 80 / 100
        item_quantity_max = item_quantity * 120 / 100
        return item_quantity_min, item_quantity_max


@dataclass
class EquipmentDropInfo:
    drop_chance: int
    bonus_critical_chance: int
    base_weapon_damage: int
    slots_modifier: int
    slots_range: list[int]
    max_ability_rolls_modifier: int
    max_ability_rolls_range: list[int]
    added_to_inventory: bool
    ability_lists: dict[EquipmentType, dict[Character, list[Autoability | None]]] = field(
        default_factory=dict)

    def __post_init__(self) -> None:
        for t in EquipmentType:
            char_lists = self.ability_lists[t] = {}
            for c in tuple(Character)[:7]:
                char_lists[c] = [None for _ in range(8)]


@dataclass
class Monster:
    index: int
    name: str
    stats: dict[Stat, int]
    overkill_threshold: int
    armored: bool
    immune_to_percentage_damage: bool
    immune_to_life: bool
    immune_to_sensor: bool
    immune_to_scan: bool
    immune_to_physical_damage: bool
    immune_to_magical_damage: bool
    immune_to_damage: bool
    immune_to_delay: bool
    immune_to_slice: bool
    immune_to_bribe: bool
    poison_tick_damage: int
    elemental_affinities: dict[Element, ElementalAffinity]
    status_resistances: dict[Status, int]
    auto_statuses: list[Status]
    doom_turns: int
    zanmato_level: int
    gil: int
    ap: dict[KillType, int]
    item_1: ItemDropInfo
    item_2: ItemDropInfo
    steal: ItemStealInfo
    bribe: ItemBribeInfo
    equipment: EquipmentDropInfo
    zones: list[str] = field(default_factory=list)
    forced_action: Action = None
    actions: dict[str, Action] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.name


def parse_monsters_file(file_path: str) -> dict[str, list[int]]:
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data = file_object.read()
    monsters_data = [[int(b, 16) for b in line.split(',')]
                     for line in data.splitlines()]
    monsters: dict[str, list[int]] = {}
    for monster_index, monster in enumerate(monsters_data):
        if monster_index in MONSTER_NAMES:
            monster_id = stringify(MONSTER_NAMES[monster_index])
        else:
            monster_id = stringify(bytes_to_string(monster, 408))
        # if the name is already in the dictionary
        # appends it with an underscore and a number
        # from 2 to 8
        if monster_id in monsters:
            for i in count(2):
                new_name = f'{monster_id}_{i}'
                if new_name in monsters:
                    continue
                monster_id = new_name
                break
        monsters[monster_id] = monster
    return monsters


def _patch_monsters_actions(file_path: str) -> None:
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data: dict[str, list[dict[str, str | int]]] = json.load(file_object)

    for monster in chain(MONSTERS.values(), MONSTERS_HD.values()):
        index = f'm{monster.index:03}'
        for action_data in data[index]:
            actions_file_id = action_data['actions_file']
            actions_file = ACTIONS_FILES_BY_ID[actions_file_id]
            action_id: int = action_data['action_id']
            action = deepcopy(actions_file[action_id])

            target: str = action_data['target']
            try:
                action.target = TargetType(target)
            except ValueError:
                try:
                    action.target = Character(target)
                except ValueError:
                    try:
                        action.target = MonsterSlot(int(target[1:]) - 1)
                    except ValueError:
                        continue

            if action.name != action_data['name']:
                action.name = action_data['name']
            action_name = stringify(action.name)
            if action_name in monster.actions:
                action.name += f' {action.target}'
                action_name = stringify(action.name)

            monster.actions[action_name] = action


def _get_monsters(monsters_data: dict[str, list[int]]) -> dict[str, Monster]:
    """Get a Monster from its data."""
    monsters = {}
    for index, (monster_id, monster_data) in enumerate(monsters_data.items()):
        if index in MONSTER_NAMES:
            monster_name = MONSTER_NAMES[index]
        else:
            monster_name = bytes_to_string(monster_data, 408)
        for i in range(16):
            if monster_name.endswith(f'{i}'):
                continue
            if monster_id.endswith(f'_{i}'):
                monster_name += f'#{i}'
                break

        stats = {
            Stat.HP: add_bytes(*monster_data[20:24]),
            Stat.MP: add_bytes(*monster_data[24:28]),
            Stat.STRENGTH: monster_data[32],
            Stat.DEFENSE: monster_data[33],
            Stat.MAGIC: monster_data[34],
            Stat.MAGIC_DEFENSE: monster_data[35],
            Stat.AGILITY: monster_data[36],
            Stat.LUCK: monster_data[37],
            Stat.EVASION: monster_data[38],
            Stat.ACCURACY: monster_data[39],
        }
        overkill_threshold = add_bytes(*monster_data[28:32])

        armored = bool(monster_data[40] & 0b00000001)
        immune_to_percentage_damage = bool(monster_data[40] & 0b00000010)
        immune_to_life = bool(monster_data[40] & 0b00000100)
        immune_to_sensor = bool(monster_data[40] & 0b00001000)
        immune_to_scan = bool(monster_data[40] & 0b00010000)
        immune_to_physical_damage = bool(monster_data[40] & 0b00100000)
        immune_to_magical_damage = bool(monster_data[40] & 0b01000000)
        immune_to_damage = bool(monster_data[40] & 0b10000000)
        immune_to_delay = bool(monster_data[41] & 0b00000001)
        immune_to_slice = bool(monster_data[41] & 0b00000010)
        immune_to_bribe = bool(monster_data[41] & 0b00000100)

        poison_tick_damage = stats[Stat.HP] * monster_data[42] // 100

        elemental_affinities: dict[Element, ElementalAffinity] = {}
        for i, element in enumerate(Element):
            if monster_data[43] & (1 << i):
                elemental_affinities[element] = ElementalAffinity.ABSORBS
            elif monster_data[44] & (1 << i):
                elemental_affinities[element] = ElementalAffinity.IMMUNE
            elif monster_data[45] & (1 << i):
                elemental_affinities[element] = ElementalAffinity.RESISTS
            elif monster_data[46] & (1 << i):
                elemental_affinities[element] = ElementalAffinity.WEAK
            else:
                elemental_affinities[element] = ElementalAffinity.NEUTRAL

        status_resistances: dict[Status, int] = {}
        for i, status in enumerate(Status, 47):
            if i > 71:
                break
            status_resistances[status] = monster_data[i]

        auto_statuses_bytes = add_bytes(*monster_data[72:78])
        auto_statuses: list[Status] = []
        for i, status in enumerate(Status):
            if i > 14:
                i += 4
            if i > 28:
                i += 3
            if i > 35:
                i += 1
            if i > 46:
                break
            if auto_statuses_bytes & (1 << i):
                auto_statuses.append(status)

        status_immunities_bytes = add_bytes(*monster_data[78:80])
        for i, status in enumerate(tuple(Status)[25:39]):
            if i > 3:
                i += 1
            if status_immunities_bytes & (1 << i):
                status_resistances[status] = 255
            else:
                status_resistances[status] = 0

        action_indexes: list[int] = []
        for i in range(80, 112, 2):
            action_indexes.append(add_bytes(*monster_data[i:i+2]))
        # menu_actions = []
        # for action in action_indexes:
        #     if not action:
        #         continue
        #     action_file = ACTIONS_FILES_BY_ID.get(action >> 12, None)
        #     if action_file is None:
        #         continue
        #     action = action_file[action & 0b1111_11111111]
        #     menu_actions.append(action)

        forced_action_byte = add_bytes(*monster_data[112:114])
        if forced_action_byte:
            action_file_index = forced_action_byte >> 12
            action_file = ACTIONS_FILES_BY_ID.get(action_file_index, None)
            if action_file:
                action_index = forced_action_byte & 0b1111_11111111
                forced_action = deepcopy(action_file[action_index])
                forced_action.target = TargetType.PROVOKER
            else:
                forced_action = ACTIONS['does_nothing']
        else:
            forced_action = ACTIONS['does_nothing']

        doom_turns = monster_data[119]

        gil = add_bytes(*monster_data[128:130])
        ap = {
            KillType.NORMAL: add_bytes(*monster_data[130:132]),
            KillType.OVERKILL: add_bytes(*monster_data[132:134]),
        }
        # ronsoRage = add_bytes(*monster_data[134:136])
        item_1 = ItemDropInfo(drop_chance=monster_data[136])
        if monster_data[141] == 32:
            item_1.items[KillType.NORMAL, Rarity.COMMON] = ItemDrop(
                ITEMS[monster_data[140]], monster_data[148], False)
        if monster_data[143] == 32:
            item_1.items[KillType.NORMAL, Rarity.RARE] = ItemDrop(
                ITEMS[monster_data[142]], monster_data[149], True)
        if monster_data[153] == 32:
            item_1.items[KillType.OVERKILL, Rarity.COMMON] = ItemDrop(
                ITEMS[monster_data[152]], monster_data[160], False)
        if monster_data[155] == 32:
            item_1.items[KillType.OVERKILL, Rarity.RARE] = ItemDrop(
                ITEMS[monster_data[154]], monster_data[161], True)

        item_2 = ItemDropInfo(drop_chance=monster_data[137])
        if monster_data[145] == 32:
            item_2.items[KillType.NORMAL, Rarity.COMMON] = ItemDrop(
                ITEMS[monster_data[144]], monster_data[150], False)
        if monster_data[147] == 32:
            item_2.items[KillType.NORMAL, Rarity.RARE] = ItemDrop(
                ITEMS[monster_data[146]], monster_data[151], True)
        if monster_data[157] == 32:
            item_2.items[KillType.OVERKILL, Rarity.COMMON] = ItemDrop(
                ITEMS[monster_data[156]], monster_data[162], False)
        if monster_data[159] == 32:
            item_2.items[KillType.OVERKILL, Rarity.RARE] = ItemDrop(
                ITEMS[monster_data[158]], monster_data[163], True)

        steal = ItemStealInfo(base_chance=monster_data[138])
        if monster_data[165] == 32:
            steal.items[Rarity.COMMON] = ItemDrop(
                ITEMS[monster_data[164]], monster_data[168], False)
        if monster_data[167] == 32:
            steal.items[Rarity.RARE] = ItemDrop(
                ITEMS[monster_data[166]], monster_data[169], True)
        bribe = ItemBribeInfo(monster_hp=stats[Stat.HP])
        if monster_data[171] == 32:
            bribe.item = ItemDrop(
                ITEMS[monster_data[170]], monster_data[172], False)
        equipment = EquipmentDropInfo(
            drop_chance=monster_data[139],
            bonus_critical_chance=monster_data[175],
            base_weapon_damage=monster_data[176],
            slots_modifier=monster_data[173],
            slots_range=[],
            max_ability_rolls_modifier=monster_data[177],
            max_ability_rolls_range=[],
            added_to_inventory=bool(monster_data[174]),
        )

        for rng_roll in range(8):
            slots = (equipment.slots_modifier + rng_roll - 4) // 4
            slots = min(max(1, slots), 4)
            equipment.slots_range.append(slots)
            ab_rolls = (equipment.max_ability_rolls_modifier + rng_roll - 4) // 8
            ab_rolls = max(0, ab_rolls)
            equipment.max_ability_rolls_range.append(ab_rolls)

        for c, base_address in zip(Character, range(178, 371, 32)):
            for t, type_offset in zip(EquipmentType, (0, 16)):
                for ability_offset in range(8):
                    address = base_address + (ability_offset * 2) + type_offset
                    if monster_data[address + 1] != 128:
                        continue
                    autoability = AUTOABILITIES[monster_data[address]]
                    equipment.ability_lists[t][c][ability_offset] = autoability

        zanmato_level = monster_data[402]
        monster = Monster(
            index=index,
            name=monster_name,
            stats=stats,
            overkill_threshold=overkill_threshold,
            armored=armored,
            immune_to_percentage_damage=immune_to_percentage_damage,
            immune_to_life=immune_to_life,
            immune_to_sensor=immune_to_sensor,
            immune_to_scan=immune_to_scan,
            immune_to_physical_damage=immune_to_physical_damage,
            immune_to_magical_damage=immune_to_magical_damage,
            immune_to_damage=immune_to_damage,
            immune_to_delay=immune_to_delay,
            immune_to_slice=immune_to_slice,
            immune_to_bribe=immune_to_bribe,
            poison_tick_damage=poison_tick_damage,
            elemental_affinities=elemental_affinities,
            status_resistances=status_resistances,
            auto_statuses=auto_statuses,
            doom_turns=doom_turns,
            zanmato_level=zanmato_level,
            gil=gil,
            ap=ap,
            item_1=item_1,
            item_2=item_2,
            steal=steal,
            bribe=bribe,
            equipment=equipment,
            forced_action=forced_action,
        )
        monsters[monster_id] = monster
    return monsters


def get_monsters_dict() -> dict[str, Monster]:
    if Configs.game_version in (GameVersion.HD, GameVersion.PS2INT):
        return MONSTERS_HD
    return MONSTERS


MONSTER_NAMES = {
    163: 'Possessed Valefor',
    164: 'Possessed Ifrit',
    165: 'Possessed Ixion',
    166: 'Possessed Shiva',
    167: 'Possessed Bahamut',
    168: 'Possessed Anima',
    169: 'Possessed Yojimbo',
    178: 'Possessed Cindy',
    179: 'Possessed Sandy',
    180: 'Possessed Mindy',
    334: 'Dark Valefor',
    335: 'Dark Ifrit',
    336: 'Dark Ixion',
    337: 'Dark Shiva',
    338: 'Dark Bahamut',
    339: 'Dark Anima',
    340: 'Dark Yojimbo',
    341: 'Dark Cindy',
    342: 'Dark Sandy',
    343: 'Dark Mindy',
}


MON_DATA_BIN = parse_monsters_file('data_files/ffx_mon_data.csv')
MONSTERS = _get_monsters(MON_DATA_BIN)

MON_DATA_BIN_HD = parse_monsters_file('data_files/ffx_mon_data_hd.csv')
MONSTERS_HD = _get_monsters(MON_DATA_BIN_HD)

_patch_monsters_actions('data_files/monster_actions.json')
