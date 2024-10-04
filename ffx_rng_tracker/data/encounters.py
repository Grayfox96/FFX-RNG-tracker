import csv
from dataclasses import dataclass

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
    zone: str
    label: str
    min: int
    default: int
    max: int
    continue_previous_zone: bool


def get_encounter_notes(file_path: str, seed: int) -> list[EncounterData]:
    encounters_notes = get_notes(file_path, seed)
    encounters = []
    csv_reader = csv.reader(encounters_notes.splitlines())
    for fields in csv_reader:
        while len(fields) < 6:
            fields.append('')
        name, initiative, label, minimum, default, maximum = fields
        if not name or name.startswith('#'):
            continue
        initiative = initiative.lower() == 'true'
        try:
            minimum = int(minimum)
        except ValueError:
            minimum = 1
        minimum = max(0, minimum)
        try:
            default = int(default)
        except ValueError:
            default = 1
        default = max(minimum, default)
        try:
            maximum = int(maximum)
        except ValueError:
            maximum = 1
        maximum = max(default, maximum)
        encounters.append(EncounterData(
            name=name,
            initiative=initiative,
            label=label,
            min=minimum,
            default=default,
            max=maximum,
        ))
    return encounters


def get_steps_notes(file_path: str, seed: int) -> list[StepsData]:
    steps_notes = get_notes(file_path, seed)
    steps = []
    csv_reader = csv.reader(steps_notes.splitlines())
    for fields in csv_reader:
        while len(fields) < 6:
            fields.append('')
        zone, label, minimum, default, maximum, continue_previous_zone = fields
        if not zone or zone.startswith('#'):
            continue
        try:
            minimum = int(minimum)
        except ValueError:
            minimum = 0
        minimum = max(0, minimum)
        try:
            default = int(default)
        except ValueError:
            default = 0
        default = max(minimum, default)
        try:
            maximum = int(maximum)
        except ValueError:
            maximum = 1000
        maximum = max(default, maximum)
        continue_previous_zone = continue_previous_zone.lower() == 'true'
        steps.append(StepsData(
            zone=zone,
            label=label,
            min=minimum,
            default=default,
            max=maximum,
            continue_previous_zone=continue_previous_zone,
        ))
    return steps
