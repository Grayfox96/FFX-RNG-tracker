import csv
from dataclasses import dataclass
from itertools import count

from .notes import get_notes


@dataclass
class EncounterData:
    name: str
    initiative: bool
    label: str
    min: int
    default: int
    max: int


def get_encounters(file_path: str, seed: int) -> list[EncounterData]:
    encounters_notes = get_notes(file_path, seed)
    encounters = {}
    csv_reader = csv.reader(encounters_notes.splitlines())
    for line in csv_reader:
        if line[0].startswith('#'):
            continue
        name = line[0]
        initiative = line[1].lower() == 'true'
        label = line[2]
        if not label:
            label = name
        if label in encounters:
            for i in count(2):
                new_label = f'{label} #{i}'
                if new_label not in encounters:
                    label = new_label
                    break

        try:
            minimum = max(int(line[3]), 0)
        except ValueError:
            minimum = 1
        try:
            default = max(minimum, int(line[4]))
        except ValueError:
            default = max(minimum, 1)
        try:
            maximum = max(default, int(line[5]))
        except ValueError:
            maximum = max(default, 1)
        encounters[label] = EncounterData(
            name=name,
            initiative=initiative,
            label=label,
            min=minimum,
            default=default,
            max=maximum,
        )
    return list(encounters.values())
