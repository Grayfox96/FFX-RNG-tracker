import csv
from typing import Dict, Iterator, List, Optional, Tuple, Union

from .data.constants import RNG_CONSTANTS_1, RNG_CONSTANTS_2
from .data.file_functions import get_resource_path
from .errors import InvalidDamageValueError, SeedNotFoundError

DmgValues = Tuple[int, int, int, int, int, int]
SeedInfo = Union[DmgValues, int]


class FFXRNGTracker:
    """"""

    def __init__(self, seed_info: SeedInfo) -> None:
        self.seed_info = seed_info
        if isinstance(seed_info, (tuple, list)) and len(seed_info) >= 6:
            self.damage_values = seed_info
            # checks for valid damage values
            self.check_damage_values()
            # retrieves the 68 initial rng seeds values and the seed number
            self.rng_initial_values, self.seed_number = self.get_rng_seed()
        elif isinstance(seed_info, int):
            self.seed_number = seed_info
            self.rng_initial_values = self.get_rng_array()
        else:
            raise SeedNotFoundError(f'Invalid seed information {seed_info}')

        # get rng generators
        # 1: encouter formations and preempt/ambush
        # 10: drop/steal chance
        # 11: rare item chance
        # 12: equipment owner, type, number of slots and abilities
        # 13: abilities
        # 20-35: damage/crit/escape chance
        # 36-51: hit chance
        # 52-67: status landing chance
        self._rng_generators = tuple(
            [self.get_rng_generator(i) for i in range(68)])
        # create a list of lists used to store rng values
        self._rng_arrays = [list() for _ in range(68)]
        self._rng_current_positions = [0 for _ in range(68)]
        # create a list used to store Events
        self.events_sequence = []
        # yojimbo compatibility
        self.compatibility = 128

    def __repr__(self) -> str:
        string = (f'{type(self).__name__}('
                  f'seed_info=({self.seed_info}))')
        return string

    def check_damage_values(self) -> Dict[str, Dict[int, int]]:
        """Checks if the damage values are valid."""
        possible_values = {
            'tidus': (
                125, 126, 127, 128, 129, 130, 131, 132, 133,
                134, 135, 136, 137, 138, 139, 140, 141,
            ),
            'auron': (
                260, 261, 262, 263, 264, 266, 267, 268, 269, 270, 271,
                272, 273, 274, 275, 276, 278, 279, 280, 281, 282, 283,
                284, 285, 286, 287, 288, 289, 291, 292, 293, 294,
            ),
        }

        for i in range(0, 5, 2):
            auron_value = self.damage_values[i]
            tidus_value = self.damage_values[i + 1]
            if auron_value not in possible_values['auron']:
                if auron_value // 2 not in possible_values['auron']:
                    raise InvalidDamageValueError(
                        f'Invalid damage value for Auron: {auron_value}')
                else:
                    self.damage_values[i] = self.damage_values[i] // 2

            if tidus_value not in possible_values['tidus']:
                if tidus_value // 2 not in possible_values['tidus']:
                    raise InvalidDamageValueError(
                        f'Invalid damage value for Tidus: {tidus_value}')
                else:
                    self.damage_values[i + 1] = self.damage_values[i + 1] // 2

    def get_rng_seed(self) -> Tuple[List[int], int]:
        """Retrieves the initial rng array values."""
        damage_values = [str(i) for i in self.damage_values]
        absolute_file_path = get_resource_path('data/ffxhd_raw_rng_arrays.csv')
        with open(absolute_file_path) as file_object:
            file_reader = csv.reader(file_object, delimiter=',')
            # skips first line
            next(file_reader)
            seed_number = 0
            for seed in file_reader:
                seed_number += 1
                # first 6 values of the array are the damage values
                if damage_values == seed[:6]:
                    current_seed_values = [int(value) for value in seed[6:]]
                    return current_seed_values, seed_number
        # if no seed found
        raise SeedNotFoundError('Seed not found.')

    @staticmethod
    def s32(integer: int) -> int:
        integer = integer & 0xffffffff
        return (integer ^ 0x80000000) - 0x80000000

    def get_rng_array(self) -> List[int]:
        """Calculates the starting values of the rng arrays."""
        rng_value = self.s32(self.seed_number)
        initial_values = []
        for _ in range(68):
            rng_value = self.s32(self.s32(rng_value * 0x5d588b65) + 0x3c35)
            rng_value = self.s32((rng_value >> 0x10) + (rng_value << 0x10))
            initial_values.append(rng_value & 0x7fffffff)
        return initial_values

    def get_rng_generator(self, rng_index: int) -> Iterator[int]:
        """Returns a generator object that yields rng values
        for a given rng index.
        """
        rng_value = self.s32(self.rng_initial_values[rng_index])
        rng_constant_1 = RNG_CONSTANTS_1[rng_index]
        rng_constant_2 = RNG_CONSTANTS_2[rng_index]

        while True:
            rng_value = self.s32(rng_value * rng_constant_1 ^ rng_constant_2)
            rng_value = self.s32((rng_value >> 0x10) + (rng_value << 0x10))
            yield rng_value & 0x7fffffff

    def advance_rng(self, index: int) -> int:
        """Advances the position of the given rng index and returns
        the next value for that index.
        """
        array = self._rng_arrays[index]
        position = self._rng_current_positions[index]
        self._rng_current_positions[index] = position + 1
        try:
            rng_value = array[position]
        except IndexError:
            rng_value = next(self._rng_generators[index])
            array.append(rng_value)
        return rng_value

    def reset(self) -> None:
        """Sets the state of some variables to their starting position."""
        self._rng_current_positions = [0 for _ in range(68)]
        self.events_sequence.clear()
        self.compatibility = 128


def get_tracker(seed_info: Optional[SeedInfo] = None) -> FFXRNGTracker:
    if seed_info is not None:
        get_tracker._tracker = FFXRNGTracker(seed_info)
    try:
        return get_tracker._tracker
    except AttributeError:
        raise
