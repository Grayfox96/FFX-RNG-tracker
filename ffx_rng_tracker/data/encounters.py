import csv
from typing import Dict, Tuple, Union

from ..data.constants import EncounterCondition
from .file_functions import get_resource_path

Enc = Dict[str, Union[str, bool, EncounterCondition, None]]


def _get_encounters(file_path: str) -> Tuple[Enc]:
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        file_reader = csv.reader(file_object, delimiter=',')
        # skips first line
        next(file_reader)
        encounters = []
        for line in file_reader:
            encounter = {}
            encounter['enc_type'] = line[0]
            encounter['name'] = line[1]
            encounter['initiative'] = line[2] == '1'
            try:
                encounter['forced_condition'] = EncounterCondition(line[3])
            except ValueError:
                encounter['forced_condition'] = None
            encounters.append(encounter)
    return tuple(encounters)


ANY_ENCOUNTERS = _get_encounters('data/any_encounters.csv')
