import json
from dataclasses import dataclass

from .file_functions import get_resource_path
from .monsters import MONSTERS, Monster

Formation = list[Monster]


@dataclass
class Formations:
    set_formation: dict[str, Formation]
    simulated: dict[str, list[Monster]]
    random: dict[str, list[Formation]]


def _get_formations(file_path: str) -> Formations:
    """Retrieves the encounter formations."""
    absolute_file_path = get_resource_path(file_path)
    with open(absolute_file_path) as file_object:
        formations: dict[str, dict] = json.loads(file_object.read())
    set_formation = {}
    for encounter, formation in formations['set'].items():
        set_formation[encounter] = [MONSTERS[m] for m in formation]

    simulated = {}
    for zone, monsters in formations['simulation'].items():
        zone = f'Simulation ({zone})'
        simulated[zone] = [MONSTERS[m] for m in monsters]

    random = {}
    for zone, formations in formations['random'].items():
        random[zone] = [[MONSTERS[m] for m in f]
                        for f in formations]

    return Formations(set_formation, simulated, random)


FORMATIONS = _get_formations('data/formations.json')
