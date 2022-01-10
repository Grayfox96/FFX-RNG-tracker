import csv
import os
import sys
from typing import Iterable

from ..errors import InvalidDamageValueError, SeedNotFoundError
from ..tracker import FFXRNGTracker
from ..utils import s32
from .file_functions import get_resource_path


def get_seed(damage_values: Iterable[int]) -> int:
    if len(damage_values) < DAMAGE_VALUES_NEEDED:
        raise SeedNotFoundError(
            f'Need at least {DAMAGE_VALUES_NEEDED} damage values')
    damage_values = damage_values[:DAMAGE_VALUES_NEEDED]

    damage_values_indexes = []
    for i, damage_value in enumerate(damage_values):
        if i in (0, 2, 4) or i >= 6:
            character = 'auron'
        else:
            character = 'tidus'
        try:
            damage_value_index = _DAMAGE_VALUES[character].index(damage_value)
        except ValueError:
            if damage_value % 2 != 0:
                raise InvalidDamageValueError(
                    f'Invalid damage value for {character}: {damage_value}')
            try:
                damage_value_index = _DAMAGE_VALUES[character].index(
                    damage_value // 2)
            except ValueError:
                raise InvalidDamageValueError(
                    f'Invalid damage value for {character}: {damage_value}')
        damage_values_indexes.append(f'{damage_value_index:02}')

    damage_indexes_as_string = ''.join(damage_values_indexes)

    if '-ps2' in sys.argv:
        absolute_file_path = get_resource_path(_PS2_SEEDS_FILE_PATH)
    else:
        absolute_file_path = get_resource_path(_SEEDS_FILE_PATH)
    with open(absolute_file_path) as file_object:
        seeds = csv.reader(file_object, delimiter=',')
        for line in seeds:
            if line[0].startswith(damage_indexes_as_string):
                break
        else:
            raise SeedNotFoundError('Seed not found')
        seed = int(line[1])
    return seed


def datetime_to_seed(datetime: int, frames: int) -> int:
    seed = s32((datetime + 1) * (s32(frames) + 1))
    seed = s32(s32(seed * 1108104919) + 11786)
    seed = s32(s32(seed * 1566083941) + 15413)
    seed = s32(s32(seed >> 16) + s32(seed << 16))
    if seed >= 0:
        return seed
    else:
        return 0x100000000 + seed


def make_seeds_file(file_path: str, frames: int) -> None:
    print('Calculating damage rolls for every possible seed'
          f' up to frame {frames}.')
    damage_rolls = []
    seeds = []
    rng_tracker = FFXRNGTracker(0)
    for frame in range(frames):
        if frame % 60 == 0:
            print(f'\r{frame}/{frames}', end='')
        for date_time in range(256):
            seed = datetime_to_seed(date_time, frame)
            rng_tracker.__init__(seed)
            auron_rolls = [rng_tracker.advance_rng(22) for _ in range(37)]
            tidus_rolls = [rng_tracker.advance_rng(20) for _ in range(7)]
            indexes = []
            # first encounter
            # get 3 damage rolls from auron and tidus
            for i in range(1, 6, 2):
                indexes.append(auron_rolls[i] & 31)
                tidus_damage = _DAMAGE_VALUES['tidus'][tidus_rolls[i] & 31]
                indexes.append(_DAMAGE_VALUES['tidus'].index(tidus_damage))
            # second encounter after dragon fang
            # get 2 damage rolls from auron
            for i in range(32, 35, 2):
                indexes.append(auron_rolls[i] & 31)
            damage_rolls.append(''.join([f'{n:02}' for n in indexes]))
            seeds.append(str(seed))
    print(f'\r{frames}/{frames}')
    data = '\n'.join([f'{d},{s}' for d, s in zip(damage_rolls, seeds)])
    with open(get_resource_path(file_path), 'w') as file:
        file.write(data)
    print('Done!')


_SEEDS_FILE_PATH = 'data/seeds.csv'
_PS2_SEEDS_FILE_PATH = 'data/ps2_seeds.csv'

_DAMAGE_VALUES = {
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

PS2_FROM_BOOT_FRAMES = 60 * 60 * 3
HD_FROM_BOOT_FRAMES = 1

if '-ps2' in sys.argv:
    DAMAGE_VALUES_NEEDED = 8
else:
    DAMAGE_VALUES_NEEDED = 6

if not os.path.exists(get_resource_path(_SEEDS_FILE_PATH)):
    print('Seeds file not found.')
    make_seeds_file(_SEEDS_FILE_PATH, HD_FROM_BOOT_FRAMES)

if '-ps2' in sys.argv:
    if not os.path.exists(get_resource_path(_PS2_SEEDS_FILE_PATH)):
        print('Seeds file for ps2 not found.')
        make_seeds_file(_PS2_SEEDS_FILE_PATH, PS2_FROM_BOOT_FRAMES)