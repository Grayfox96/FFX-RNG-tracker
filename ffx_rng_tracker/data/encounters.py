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


@dataclass
class StepsData:
    name: str
    label: str
    min: int
    default: int
    max: int
    continue_previous_zone: bool


def get_encounter_notes(file_path: str, seed: int) -> list[EncounterData]:
    encounters_notes = get_notes(file_path, seed)
    encounters = {}
    csv_reader = csv.reader(encounters_notes.splitlines())
    for line in csv_reader:
        if line[0].startswith('#'):
            continue
        name = line[0]
        initiative = line[1].lower() == 'true'
        try:
            label = line[2]
        except IndexError:
            label = name
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
        except (ValueError, IndexError):
            minimum = 1
        try:
            default = max(minimum, int(line[4]))
        except (ValueError, IndexError):
            default = max(minimum, 1)
        try:
            maximum = max(default, int(line[5]))
        except (ValueError, IndexError):
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


def get_steps_notes(file_path: str, seed: int) -> list[StepsData]:
    steps_notes = get_notes(file_path, seed)
    steps = {}
    csv_reader = csv.reader(steps_notes.splitlines())
    for line in csv_reader:
        if line[0].startswith('#'):
            continue
        name = line[0]
        try:
            label = line[1]
        except IndexError:
            label = name
        if not label:
            label = name
        if label in steps:
            for i in count(2):
                new_label = f'{label} #{i}'
                if new_label not in steps:
                    label = new_label
                    break
        try:
            minimum = max(int(line[2]), 0)
        except (ValueError, IndexError):
            minimum = 0
        try:
            default = max(minimum, int(line[3]))
        except (ValueError, IndexError):
            default = max(minimum, 1)
        try:
            maximum = max(default, int(line[4]))
        except (ValueError, IndexError):
            maximum = max(default, 1)
        try:
            continue_previous_zone = line[5].lower() == 'true'
        except IndexError:
            continue_previous_zone = False
        steps[label] = StepsData(
            name=name,
            label=label,
            min=minimum,
            default=default,
            max=maximum,
            continue_previous_zone=continue_previous_zone,
        )
    return list(steps.values())
