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

        min = int(line[3])
        default = int(line[4])
        max = int(line[5])
        encounters[label] = EncounterData(
            name=name,
            initiative=initiative,
            label=label,
            min=min,
            default=default,
            max=max,
        )
    return list(encounters.values())
