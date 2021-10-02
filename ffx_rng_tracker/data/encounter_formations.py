import csv

from .file_functions import get_resource_path
from .monsters import MONSTERS, Monster

Formation = list[Monster]


def _get_formations(file_path: str) -> dict[str, list[Formation]]:
    """Retrieves the encounter formations."""
    formations = {}
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        file_reader = csv.reader(file_object, delimiter=',')
        next(file_reader)
        for line in file_reader:
            zone = line[0]
            formations[zone] = []
            for formation in line[1:]:
                formation = [MONSTERS[m] for m in formation.split('+')]
                formations[zone].append(formation)
    return formations


FORMATIONS = _get_formations('data/formations.csv')
