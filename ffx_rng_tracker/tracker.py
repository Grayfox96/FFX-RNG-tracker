from typing import Iterator

from .data.constants import (BASE_COMPATIBILITY, RNG_CONSTANTS_1,
                             RNG_CONSTANTS_2)
from .utils import s32


class FFXRNGTracker:
    """"""

    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng_initial_values = self.get_rng_array()

        # get rng generators
        # 0: encounter chance
        # 1: encouter formations and preempt/ambush
        # 4: monster targeting
        # 5: multihit actions targeting
        # 9: screenshake
        # 10: drop/steal chance
        # 11: rare item chance
        # 12: equipment owner, type, number of slots and abilities
        # 13: abilities
        # 14: camera
        # 17: yojimbo motivation
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
        self.compatibility = BASE_COMPATIBILITY

    def __repr__(self) -> str:
        return f'{type(self).__name__}(seed=({self.seed}))'

    def get_rng_array(self) -> list[int]:
        """Calculates the starting values of the rng arrays."""
        rng_value = s32(self.seed)
        initial_values = []
        for _ in range(68):
            rng_value = s32(s32(rng_value * 0x5d588b65) + 0x3c35)
            rng_value = s32((rng_value >> 0x10) + (rng_value << 0x10))
            initial_values.append(rng_value & 0x7fffffff)
        return initial_values

    def get_rng_generator(self, rng_index: int) -> Iterator[int]:
        """Returns a generator object that yields rng values
        for a given rng index.
        """
        rng_value = s32(self.rng_initial_values[rng_index])
        rng_constant_1 = RNG_CONSTANTS_1[rng_index]
        rng_constant_2 = RNG_CONSTANTS_2[rng_index]

        while True:
            rng_value = s32(rng_value * rng_constant_1 ^ rng_constant_2)
            rng_value = s32((rng_value >> 0x10) + (rng_value << 0x10))
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
        self.compatibility = BASE_COMPATIBILITY
