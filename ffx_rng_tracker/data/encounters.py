import csv

from .file_functions import get_resource_path


def _get_encounters(file_path: str) -> tuple[dict[str, str]]:
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        file_reader = csv.reader(file_object, delimiter=',')
        # skips first line
        next(file_reader)
        encounters = []
        for line in file_reader:
            encounter = {
                'name': line[0],
                'type': line[1],
                'initiative': line[2],
                'label': line[3],
                'min': line[4],
                'default': line[5],
                'max': line[6],
            }
            encounters.append(encounter)
    return tuple(encounters)


ANY_ENCOUNTERS = _get_encounters('data/any_encounters.csv')
