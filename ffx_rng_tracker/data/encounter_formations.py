import json
from dataclasses import dataclass, field

from .file_functions import get_resource_path
from .monsters import MONSTERS, Monster

Formation = list[Monster]


@dataclass
class Zone:
    name: str
    formations: list[Formation]
    grace_period: int = field(default=0)
    threat_modifier: int = field(default=0)

    def __str__(self) -> str:
        return self.name


@dataclass
class Boss:
    name: str
    formation: Formation


@dataclass
class Formations:
    bosses: dict[str, Boss]
    simulated: dict[str, tuple[str, list[Monster]]]
    zones: dict[str, Zone]


def _get_formations(file_path: str) -> Formations:
    """Retrieves the encounter formations."""
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        formations: dict[str, dict] = json.loads(file_object.read())
    set_formation = {}
    for encounter, data in formations['set'].items():
        set_formation[encounter] = Boss(
            data['name'],
            [MONSTERS[m] for m in data['formation']]
        )

    simulated = {}
    for encounter, data in formations['simulation'].items():
        name = f'Simulation ({data["name"]})'
        key = name.lower().replace(' ', '_')
        simulated[key] = (
            name,
            [MONSTERS[m] for m in data['monsters']]
        )

    random = {}
    for encounter, data in formations['random'].items():
        random[encounter] = Zone(
            name=data['name'],
            formations=[[MONSTERS[m] for m in f] for f in data['formations']],
        )

    return Formations(set_formation, simulated, random)


FORMATIONS = _get_formations('data/formations.json')
