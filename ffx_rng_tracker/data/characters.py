import json
from dataclasses import dataclass

from ..utils import open_cp1252
from .autoabilities import (ELEMENTAL_EATERS, ELEMENTAL_PROOFS,
                            ELEMENTAL_WARDS, STATUS_PROOFS, STATUS_WARDS)
from .constants import (Autoability, Character, Element, ElementalAffinity,
                        EquipmentType, Stat, Status)
from .equipment import Equipment
from .file_functions import get_resource_path


@dataclass(frozen=True)
class DefaultCharacterState:
    character: Character
    index: int
    stats: dict[Stat, int]
    weapon: Equipment
    armor: Equipment


@dataclass
class CharacterState:
    defaults: DefaultCharacterState

    def __str__(self) -> str:
        return str(self.character)

    def __post_init__(self) -> None:
        self.reset()

    @property
    def character(self) -> Character:
        return self.defaults.character

    @property
    def index(self) -> int:
        return self.defaults.index

    def set_stat(self, stat: Stat, value: int) -> None:
        match stat:
            case Stat.HP:
                max_value = 99999
            case Stat.MP:
                max_value = 9999
            case Stat.CHEER | Stat.FOCUS:
                max_value = 5
            case Stat():
                max_value = 255
            case _:
                raise ValueError(f'Invalid stat name: {stat}')
        value = min(max(value, 0), max_value)
        self.stats[stat] = value

    @property
    def weapon(self) -> Equipment:
        return self._weapon

    @weapon.setter
    def weapon(self, equipment: Equipment) -> None:
        self._weapon = equipment

    @property
    def armor(self) -> Equipment:
        return self._armor

    @armor.setter
    def armor(self, equipment: Equipment) -> None:
        for ability in equipment.abilities:
            if ability in ELEMENTAL_WARDS:
                element = ELEMENTAL_WARDS[ability]
                self.elemental_affinities[element] = ElementalAffinity.RESISTS
            elif ability in ELEMENTAL_PROOFS:
                element = ELEMENTAL_PROOFS[ability]
                self.elemental_affinities[element] = ElementalAffinity.IMMUNE
            elif ability in ELEMENTAL_EATERS:
                element = ELEMENTAL_EATERS[ability]
                self.elemental_affinities[element] = ElementalAffinity.ABSORBS
            elif ability in STATUS_PROOFS:
                status = STATUS_PROOFS[ability]
                self.status_resistances[status] = 254
            elif ability in STATUS_WARDS:
                status = STATUS_WARDS[ability]
                self.status_resistances[status] = 50
        self._armor = equipment

    def reset(self) -> None:
        self.stats = self.defaults.stats.copy()
        self.elemental_affinities = {element: ElementalAffinity.NEUTRAL
                                     for element in Element}
        self.status_resistances = {s: 0 for s in Status}
        self.statuses = []
        self.weapon = Equipment(
            owner=self.defaults.weapon.owner,
            type_=self.defaults.weapon.type_,
            slots=self.defaults.weapon.slots,
            abilities=self.defaults.weapon.abilities.copy(),
            base_weapon_damage=self.defaults.weapon.base_weapon_damage,
            bonus_crit=self.defaults.weapon.bonus_crit
        )
        self.armor = Equipment(
            owner=self.defaults.armor.owner,
            type_=self.defaults.armor.type_,
            slots=self.defaults.armor.slots,
            abilities=self.defaults.armor.abilities.copy(),
            base_weapon_damage=self.defaults.armor.base_weapon_damage,
            bonus_crit=self.defaults.armor.bonus_crit
        )


def _get_characters(file_path: str) -> dict[Character, DefaultCharacterState]:
    """"""
    absolute_file_path = get_resource_path(file_path)
    with open_cp1252(absolute_file_path) as file_object:
        data: dict = json.load(file_object)
    characters = {}
    for index, (character, character_data) in enumerate(data.items()):
        character = Character(character)
        weapon_data = character_data['weapon']
        weapon = Equipment(
            owner=character,
            type_=EquipmentType.WEAPON,
            slots=weapon_data['slots'],
            abilities=[Autoability(a) for a in weapon_data['abilities']],
            base_weapon_damage=weapon_data['base_weapon_damage'],
            bonus_crit=weapon_data['bonus_crit'],
        )
        armor_data = character_data['armor']
        armor = Equipment(
            owner=character,
            type_=EquipmentType.ARMOR,
            slots=armor_data['slots'],
            abilities=[Autoability(a) for a in armor_data['abilities']],
            base_weapon_damage=16,
            bonus_crit=armor_data['bonus_crit'],
        )
        characters[character] = DefaultCharacterState(
            character=character,
            index=index,
            stats={Stat(k): v for k, v in character_data['stats'].items()},
            weapon=weapon,
            armor=armor,
        )

    return characters


CHARACTERS_DEFAULTS = _get_characters('data/characters.json')
