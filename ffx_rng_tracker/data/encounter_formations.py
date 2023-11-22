import json
from dataclasses import dataclass

from ..utils import open_cp1252, search_stringenum
from .constants import EncounterCondition
from .file_functions import get_resource_path
from .monsters import MONSTERS, MONSTERS_HD, Monster, get_monsters_dict


@dataclass
class Formation:
    monsters_names: list[str]
    forced_condition: EncounterCondition | None

    def __str__(self) -> str:
        return ', '.join([str(m) for m in self.monsters])

    @property
    def monsters(self) -> list[Monster]:
        monsters = get_monsters_dict()
        return [monsters[m] for m in self.monsters_names]


@dataclass
class Zone:
    name: str
    formations: list[Formation]
    danger_value: int

    def __post_init__(self) -> None:
        self.grace_period = self.danger_value // 2
        self.threat_modifier = self.danger_value * 4

    def __str__(self) -> str:
        return self.name


@dataclass
class Boss:
    name: str
    formation: Formation

    def __str__(self) -> str:
        return self.name


@dataclass
class Simulation:
    name: str
    monsters: Formation

    def __str__(self) -> str:
        return self.name


Formations = tuple[dict[str, Boss], dict[str, Simulation], dict[str, Zone]]


def _get_condition(condition: str) -> EncounterCondition | None:
    try:
        condition = search_stringenum(EncounterCondition, condition)
    except ValueError:
        condition = None
    return condition


def _get_formations(file_path: str) -> Formations:
    """Retrieves the encounter formations."""
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        formations: dict[str, dict] = json.load(file_object)
    bosses: dict[str, Boss] = {}
    for boss, data in formations['bosses'].items():
        formation = Formation(
            data['formation'],
            _get_condition(data['forced_condition']),
            )
        bosses[boss] = Boss(
            data['name'],
            formation,
        )

    simulations: dict[str, Simulation] = {}
    for simulation, data in formations['simulation'].items():
        monsters = Formation(
            data['monsters'],
            EncounterCondition.NORMAL,
            )
        simulations[simulation] = Simulation(
            data['name'],
            monsters,
        )

    zones: dict[str, Zone] = {}
    for zone, data in formations['zones'].items():
        encounters = []
        for encounter in data['encounters']:
            formation = Formation(
                encounter['monsters'],
                _get_condition(encounter['forced_condition'])
                )
            encounters.append(formation)
        zones[zone] = Zone(
            data['name'],
            encounters,
            data['danger_value'],
        )
        for formation in zones[zone].formations:
            for monster_name in formation.monsters_names:
                monster = MONSTERS[monster_name]
                if zones[zone].name not in monster.zones:
                    monster.zones.append(zones[zone].name)
                monster = MONSTERS_HD[monster_name]
                if zones[zone].name not in monster.zones:
                    monster.zones.append(zones[zone].name)

    return bosses, simulations, zones


BOSSES, SIMULATIONS, ZONES = _get_formations('data_files/formations.json')
FORMATIONS = BOSSES | SIMULATIONS | ZONES
