import csv
import os
from itertools import islice
from logging import getLogger
from typing import Iterable

from ..configs import Configs
from ..errors import InvalidDamageValueError, SeedNotFoundError
from ..tracker import FFXRNGTracker
from ..utils import open_cp1252
from .constants import GameVersion


def get_seed(damage_values: Iterable[int]) -> int:
    damage_values_needed = DAMAGE_VALUES_NEEDED[Configs.game_version]
    if len(damage_values) < damage_values_needed:
        raise SeedNotFoundError(
            f'Need at least {damage_values_needed} damage values')

    logger = getLogger(__name__)
    if not os.path.exists(SEEDS_DIRECTORY_PATH):
        logger.warning('Seeds files directory not found.')
        os.mkdir(SEEDS_DIRECTORY_PATH)
        logger.info(f'Created seeds file directory "{SEEDS_DIRECTORY_PATH}".')

    seeds_file_path = SEEDS_FILE_PATHS[Configs.game_version]

    if not os.path.exists(seeds_file_path):
        logger.warning('Seeds file not found.')
        make_seeds_file(
            seeds_file_path, FRAMES_FROM_BOOT[Configs.game_version])
        logger.info('Done creating seeds file.')

    damage_values = damage_values[:damage_values_needed]
    indexes = []
    for i, damage_value in enumerate(damage_values):
        if i in (0, 2, 4) or i >= 6:
            character = 'auron'
        else:
            character = 'tidus'
        try:
            index = _DAMAGE_VALUES[character].index(damage_value)
        except ValueError:
            if damage_value % 2 != 0:
                raise InvalidDamageValueError(
                    f'Invalid damage value for {character}: {damage_value}')
            try:
                index = _DAMAGE_VALUES[character].index(damage_value // 2) + 32
            except ValueError:
                raise InvalidDamageValueError(
                    f'Invalid damage value for {character}: {damage_value}')
        indexes.append(index)

    damage_indexes_as_string = ''.join([f'{n:02}' for n in indexes])

    with open_cp1252(seeds_file_path) as file_object:
        seeds = csv.reader(file_object)
        for line in seeds:
            if line[0].startswith(damage_indexes_as_string):
                break
        else:
            logger.warning(f'Failed to find seed from DVs "{damage_values}".')
            raise SeedNotFoundError('Seed not found')
        seed = int(line[1])
    logger.info(f'Found seed {seed} from DVs "{damage_values}"')
    return seed


def datetime_to_seed(datetime: int, frames: int) -> int:
    seed = (datetime + 1) * (frames + 1)
    seed = (seed * 0x420C56D7 + 0x2E0A) * 0x5D588B65 + 0x3C35
    seed = ((seed & 0xffffffff) ^ 0x80000000) - 0x80000000
    return ((seed >> 0x10) + (seed << 0x10)) & 0xffffffff


def make_seeds_file(file_path: str, frames: int) -> None:
    logger = getLogger(__name__)
    logger.info(f'Calculating seeds up to frame {frames}.')
    if os.path.exists(file_path):
        logger.warning(f'Seeds file named "{file_path}" already exists.')
        return
    tidus_damage_rolls = _DAMAGE_VALUES['tidus']
    lines = []
    seeds = set()
    tracker = FFXRNGTracker(0)
    for frame in range(frames):
        for date_time in range(256):
            seed = datetime_to_seed(date_time, frame)
            tracker.seed = seed
            if seed in seeds:
                continue
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
                tidus_damage = tidus_damage_rolls[tidus_rolls[i] & 31]
                tidus_damage_index = tidus_damage_rolls.index(
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
            lines.append(
                ''.join([f'{n:02}' for n in indexes]) + ',' + str(seed))
            seeds.add(seed)
    data = '\n'.join(lines)
    with open_cp1252(file_path, 'w') as file:
        file.write(data)
    logger.info(f'Done calculating seeds up to frame {frames}.')


_DAMAGE_VALUES: dict[str, tuple[int]] = {
    'auron': (
        260, 261, 262, 263, 264, 266, 267, 268, 269, 270, 271,
        272, 273, 274, 275, 276, 278, 279, 280, 281, 282, 283,
        284, 285, 286, 287, 288, 289, 291, 292, 293, 294,
    ),
    'tidus': (
        125, 126, 126, 127, 127, 128, 128, 129, 129, 130, 130,
        131, 131, 132, 132, 133, 134, 134, 135, 135, 136, 136,
        137, 137, 138, 138, 139, 139, 140, 140, 141, 141,
    ),
}
FRAMES_FROM_BOOT = {
    GameVersion.PS2NA: 60 * 30 * Configs.ps2_seeds_minutes,
    GameVersion.PS2INT: 60 * 30 * Configs.ps2_seeds_minutes,
    GameVersion.HD: 1,
}
DAMAGE_VALUES_NEEDED = {
    GameVersion.PS2NA: 8,
    GameVersion.PS2INT: 8,
    GameVersion.HD: 3,
}
SEEDS_DIRECTORY_PATH = 'ffx_rng_tracker_seeds'
SEEDS_FILE_PATHS = {
    GameVersion.PS2NA: SEEDS_DIRECTORY_PATH + '/ps2_seeds.csv',
    GameVersion.PS2INT: SEEDS_DIRECTORY_PATH + '/ps2_seeds.csv',
    GameVersion.HD: SEEDS_DIRECTORY_PATH + '/seeds.csv',
}
