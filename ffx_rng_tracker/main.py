from typing import Iterable, Optional, Union

from .data.seeds import get_seed
from .tracker import FFXRNGTracker

SeedInfo = Union[Iterable[int], int]


def get_tracker(seed_info: Optional[SeedInfo] = None) -> FFXRNGTracker:
    if seed_info is not None:
        if isinstance(seed_info, (tuple, list)):
            seed = get_seed(seed_info)
        elif isinstance(seed_info, int):
            seed = seed_info
        get_tracker._tracker = FFXRNGTracker(seed)
    return get_tracker._tracker
