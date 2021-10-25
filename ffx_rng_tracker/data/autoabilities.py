import csv
from dataclasses import dataclass
from typing import Tuple

from .file_functions import get_resource_path


@dataclass(frozen=True)
class Autoability:
    name: str
    gil_value: int

    def __str__(self) -> str:
        return self.name


def _get_autoabilities(file_path: str) -> Tuple[Autoability]:
    """Retrieves the abilities names and their base gil values
    used in the equipment price formula.
    """
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        abilities_file_reader = csv.reader(
            file_object, delimiter=',')
        # skips first line
        next(abilities_file_reader)
        autoabilities = []
        for line in abilities_file_reader:
            autoabilities.append(Autoability(line[1], int(line[2])))
    return tuple(autoabilities)


AUTOABILITIES = _get_autoabilities('data/auto-abilities.csv')
