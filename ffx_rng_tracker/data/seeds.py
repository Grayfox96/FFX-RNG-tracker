import os
import pprint
from collections.abc import Iterable
from itertools import islice
from logging import getLogger

from ..configs import Configs
from ..errors import InvalidDamageValueError, SeedNotFoundError
from ..tracker import FFXRNGTracker
from ..utils import open_cp1252
from .constants import GameVersion

type Node = dict[int, Node] | int
type PrunedNode = dict[str, PrunedNode] | str


def prune(node: Node) -> PrunedNode:
    """prune branches with a single child to a leaf recursively"""
    # if the node is a leaf return it
    if isinstance(node, int):
        return f'{node:010}'
    elif len(node) == 1:
        # get the only value in the dict and prune it
        k, v = next(iter(node.items()))
        child = prune(v)
        # if it got pruned to a leaf return it
        if isinstance(child, str):
            return child
        # otherwise return the node since it cant be pruned further
        return {f'{k:02}': child}
    # if there is more than one child then reduce all of them
    return {f'{k:02}': prune(v) for k, v in node.items()}


def damage_rolls_to_values(damage_rolls: Iterable[int]) -> list[int]:
    """damage rolls 1/3/5 are used to get values from _TIDUS_DAMAGE_VALUES

    drs 0/2/4/6/7 are used to get values from _AURON_DAMAGE_VALUES

    returns a list of 0-8 damage values based
    on the size of the damage_values iterable

    raises ValueError if a damage roll is not in the range 0-63
    """
    damage_values = []
    for i, damage_roll in enumerate(damage_rolls):
        if i in (0, 2, 4) or i >= 6:
            dvs = _AURON_DAMAGE_VALUES
        else:
            dvs = _TIDUS_DAMAGE_VALUES
        if 0 <= damage_roll <= 31:
            damage_values.append(dvs[damage_roll])
        elif 32 <= damage_roll <= 63:
            damage_values.append(dvs[damage_roll - 32] * 2)
        else:
            raise ValueError('Damage roll has to be an integer between 0'
                             f' and 63, value given: {damage_roll}'
                             )
    return damage_values


def damage_value_to_rolls(damage_values: Iterable[int]) -> list[int]:
    """damage values 1/3/5 are searched in _TIDUS_DAMAGE_VALUES

    dvs 0/2/4/6/7 are searched in _AURON_DAMAGE_VALUES

    returns a list of 0-8 damage rolls based
    on the size of the damage_values iterable

    raises InvalidDamageValueError if one of the items
    of damage_values is not valid
    """
    indexes = []
    for i, damage_value in enumerate(damage_values):
        if i in (0, 2, 4) or i >= 6:
            dvs = _AURON_DAMAGE_VALUES
            character = 'Auron'
        else:
            dvs = _TIDUS_DAMAGE_VALUES
            character = 'Tidus'
        try:
            index = dvs.index(damage_value)
        except ValueError:
            # check if the damage value could be from a crit
            if damage_value % 2 != 0:
                raise InvalidDamageValueError(
                    f'Invalid damage value for {character}: {damage_value}')
            try:
                index = dvs.index(damage_value // 2) + 32
            except ValueError:
                raise InvalidDamageValueError(
                    f'Invalid damage value for {character}: {damage_value}')
        indexes.append(index)
    return indexes


def get_seed_from_string(damage_values_string: str,
                         continue_search: bool = False,
                         ) -> int:
    for symbol in (',', '-', '/', '\\', '.'):
        damage_values_string = damage_values_string.replace(symbol, ' ')
    seed_info = damage_values_string.split()
    try:
        seed_info = [int(i) for i in seed_info]
    except ValueError as error:
        error = str(error).split(': ', 1)[1]
        raise SeedNotFoundError(f'{error} is not a valid damage value')
    if len(seed_info) == 0:
        raise SeedNotFoundError('Input damage values or a Seed Number first')
    elif len(seed_info) == 1:
        seed = seed_info[0]
        if 0 <= seed <= 0xffffffff:
            return seed
        raise SeedNotFoundError(
            'Seed must be an integer between 0 and 4294967295')
    return get_seed(seed_info, Configs.continue_ps2_seed_search)


def get_seed(damage_values: Iterable[int],
             continue_search: bool = False,
             ) -> int:
    """damage_values needs to have at least 3 or 8 items
    depending on what Configs.game_version is set to

    if continue_search is true when the seed is not found in the
    seeds file search_seed is called with the same dvs

    returns an integer between 0 and (2**32 - 1)

    raises SeedNotFoundError if there are less than 3 or 8 items
    in damage_values or if the seed is not found in the seeds
    file or by search_seed
    """
    dvs_needed = DAMAGE_VALUES_NEEDED[Configs.game_version]
    if len(damage_values) < dvs_needed:
        raise SeedNotFoundError(
            f'Need at least {dvs_needed} damage values')

    logger = getLogger(__name__)
    if not os.path.exists(SEEDS_DIRECTORY_PATH):
        logger.warning('Seeds files directory not found.')
        os.mkdir(SEEDS_DIRECTORY_PATH)
        logger.info(f'Created seeds file directory "{SEEDS_DIRECTORY_PATH}".')

    seeds_file_path = SEEDS_FILE_PATHS[Configs.game_version]

    if not os.path.exists(seeds_file_path):
        logger.warning('Seeds file not found.')
        make_seeds_file(
            seeds_file_path, POSSIBLE_XORED_DATETIMES[Configs.game_version],
            FRAMES_FROM_BOOT[Configs.game_version]
            )
        logger.info('Done creating seeds file.')

    damage_values = damage_values[:dvs_needed]
    damage_rolls = damage_value_to_rolls(damage_values)
    with open_cp1252(seeds_file_path) as file_object:
        seeds = file_object.read().splitlines()
    i = 0
    needle = f'{damage_rolls[i]:02}'
    for line in seeds:
        if not line.startswith(needle):
            continue
        seed = int(line[-10:])
        drs_check = get_damage_rolls(FFXRNGTracker(seed))[:dvs_needed]
        if damage_rolls == drs_check:
            logger.info(f'Found seed {seed} in seeds file'
                        f' from DVs "{damage_values}"'
                        )
            break
        i += 1
        needle += f'{damage_rolls[i]:02}'
    else:
        logger.warning(
            f'Failed to find seed in seeds file from DVs "{damage_values}".')
        if Configs.game_version is GameVersion.HD or not continue_search:
            raise SeedNotFoundError('Seed not found (seeds file exhausted)')
        seed = search_seed(damage_rolls)
        logger.info(f'Found seed {seed} from seed search'
                    f' from DVs "{damage_values}"'
                    )
    return seed


def search_seed(damage_rolls: Iterable[int]) -> int:
    """damage_rolls needs to have 8 items

    returns an integer between 0 and (2**32 - 1)

    raises SeedNotFoundError if Configs.game_version is set to HD,
    if there are less than 8 items in damage_rolls or if the seed
    is not found in the seed range
    """
    if Configs.game_version is GameVersion.HD:
        raise SeedNotFoundError('No seeds available past frame 0 on HD port.')
    dvs_needed = DAMAGE_VALUES_NEEDED[Configs.game_version]
    if len(damage_rolls) < dvs_needed:
        raise SeedNotFoundError(
            f'Need at least {dvs_needed} damage values')
    tracker = FFXRNGTracker(0)
    starting_frame = FRAMES_FROM_BOOT[Configs.game_version]
    ending_frame = starting_frame + (60 * 60 * 10)
    date_times = POSSIBLE_XORED_DATETIMES[Configs.game_version]
    logger = getLogger(__name__)
    logger.info(f'Starting seed search in frames range'
                f' {starting_frame}-{ending_frame}.')
    seeds = set()
    for frame in range(starting_frame, ending_frame):
        if frame % 3600 == 0:
            logger.debug(f'Checked up to frame {frame}.')
        for date_time in date_times:
            seed = datetime_to_seed(date_time, frame)
            if seed in seeds:
                continue
            seeds.add(seed)
            tracker.seed = seed
            if damage_rolls == get_damage_rolls(tracker):
                return seed
    raise SeedNotFoundError(f'Seed not found (searched up to frame {frame})')


def datetime_to_seed(datetime: int, frames: int) -> int:
    seed = (datetime + 1) * (frames + 1)
    seed = (seed * 0x420C56D7 + 0x2E0A) * 0x5D588B65 + 0x3C35
    seed = ((seed & 0xffffffff) ^ 0x80000000) - 0x80000000
    return ((seed >> 0x10) + (seed << 0x10)) & 0xffffffff


def get_damage_rolls(tracker: FFXRNGTracker) -> list[int]:
    """uses the tracker to calculate the 8 damage rolls
    used to retrieve a seed
    """
    tracker.rng_initial_values = tracker.get_rng_initial_values(23)
    auron_rolls = tuple(islice(tracker.get_rng_generator(22), 37))
    tidus_rolls = tuple(islice(tracker.get_rng_generator(20), 7))
    indexes = []
    # first encounter
    # get 3 damage rolls from auron and tidus
    for i in (1, 3, 5):
        auron_damage_index = auron_rolls[i] & 31
        # if auron crits the sinscale adds 32, otherwise 0
        auron_damage_index += 32 * ((auron_rolls[i + 1] % 101) < 22)
        indexes.append(auron_damage_index)
        tidus_damage = _TIDUS_DAMAGE_VALUES[tidus_rolls[i] & 31]
        tidus_damage_index = _TIDUS_DAMAGE_VALUES.index(
                    tidus_damage)
        # if tidus crits the sinscale adds 32, otherwise 0
        tidus_damage_index += 32 * ((tidus_rolls[i + 1] % 101) < 23)
        indexes.append(tidus_damage_index)
    # second encounter after dragon fang
    # get 2 damage rolls from auron
    for i in (32, 34):
        auron_damage_index = auron_rolls[i] & 31
        # if auron crits ammes adds 32, otherwise 0
        auron_damage_index += 32 * ((auron_rolls[i + 1] % 101) < 13)
        indexes.append(auron_damage_index)
    return indexes


def make_seeds_file(file_path: str,
                    date_times: list[int],
                    ending_frame: int,
                    starting_frame: int = 0,
                    ) -> None:
    """calculates damage rolls for every seed possible in a range given
    a frames range and a list of datetimes and writes them to file_path

    returns immediately if file_path already exists
    """
    logger = getLogger(__name__)
    if os.path.exists(file_path):
        logger.warning(f'Seeds file named "{file_path}" already exists.')
        return
    logger.info(f'Calculating seeds in frame range'
                f' {starting_frame}-{ending_frame}'
                f' for game version {Configs.game_version}.')
    seeds = set()
    tracker = FFXRNGTracker(0)
    root_node: Node = {}
    for frame in range(starting_frame, ending_frame):
        if frame % 3600 == 0 and frame != 0:
            logger.debug(f'Calculated up to frame {frame}.')
        for date_time in date_times:
            seed = datetime_to_seed(date_time, frame)
            if seed in seeds:
                continue
            seeds.add(seed)
            tracker.seed = seed
            *indexes, last_index = get_damage_rolls(tracker)
            node = root_node
            for index in indexes:
                node = node.setdefault(index, {})
            node[last_index] = seed
    data = (pprint.pformat(prune(root_node), width=1)
            .replace('}', '')
            .replace(',', '')
            .replace(':', '')
            .replace('{', '')
            .replace(' \'', '')
            .replace('\'', '')
            .replace('       ', '  ')
            )
    lines = data.splitlines()
    for index, line in enumerate(lines):
        count = line.count(' ')
        if count == 0:
            continue
        lines[index] = lines[index - 1][:count] + line[count:]
    data = '\n'.join(lines)
    with open_cp1252(file_path, 'w') as file:
        file.write(data)
    logger.info(f'Done calculating seeds in frame range'
                f' {starting_frame}-{ending_frame}.')


_TIDUS_DAMAGE_VALUES = (
    125, 126, 126, 127, 127, 128, 128, 129, 129, 130, 130,
    131, 131, 132, 132, 133, 134, 134, 135, 135, 136, 136,
    137, 137, 138, 138, 139, 139, 140, 140, 141, 141,
    )
_AURON_DAMAGE_VALUES = (
    260, 261, 262, 263, 264, 266, 267, 268, 269, 270, 271,
    272, 273, 274, 275, 276, 278, 279, 280, 281, 282, 283,
    284, 285, 286, 287, 288, 289, 291, 292, 293, 294,
    )
FRAMES_FROM_BOOT = {
    GameVersion.PS2NA: 60 * 60 * 10,
    GameVersion.PS2INT: 60 * 60 * 10,
    GameVersion.HD: 1,
}
POSSIBLE_XORED_DATETIMES = {
    GameVersion.PS2NA: [i for i in range(128)],
    GameVersion.PS2INT: [i for i in range(128)],
    GameVersion.HD: [i for i in range(256)],
}
DAMAGE_VALUES_NEEDED = {
    GameVersion.PS2NA: 8,
    GameVersion.PS2INT: 8,
    GameVersion.HD: 3,
}
SEEDS_DIRECTORY_PATH = 'ffx_rng_tracker_seeds'
SEEDS_FILE_PATHS = {
    GameVersion.PS2NA: SEEDS_DIRECTORY_PATH + '/ps2_seeds.dat',
    GameVersion.PS2INT: SEEDS_DIRECTORY_PATH + '/ps2_seeds.dat',
    GameVersion.HD: SEEDS_DIRECTORY_PATH + '/seeds.dat',
}
