import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from .configs import Configs
from .data.actions import YOJIMBO_ACTIONS, Action, YojimboAction
from .data.characters import CHARACTERS, Character
from .data.constants import (COMPATIBILITY_MODIFIER, HIT_CHANCE_TABLE,
                             ICV_BASE, ICV_VARIANCE, OVERDRIVE_MOTIVATION,
                             ZANMATO_LEVELS, DamageType, ElementalAffinity,
                             EncounterCondition, EquipmentSlots, EquipmentType,
                             Rarity, Stat)
from .data.encounter_formations import FORMATIONS, Formation
from .data.equipment import Equipment, EquipmentDrop
from .data.items import ItemDrop
from .data.monsters import Monster
from .main import get_tracker
from .tracker import FFXRNGTracker


@dataclass
class Event(ABC):
    """Abstract base class for all events."""
    _rng_tracker: FFXRNGTracker = field(
        default_factory=get_tracker, init=False, repr=False)

    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass
class ChangeParty(Event):
    party_formation: List[Character]

    def __str__(self) -> str:
        character_names = [c.name for c in self.party_formation]
        return f'Party changed to: {", ".join(character_names)}'


@dataclass
class Steal(Event):
    monster: Monster
    successful_steals: int
    item: Optional[ItemDrop] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.item = self._get_item()

    def __str__(self) -> str:
        string = f'Steal from {self.monster.name}: '
        if self.item:
            string += str(self.item)
        else:
            string += 'Failed'
        return string

    def _get_item(self) -> Optional[ItemDrop]:
        rng_steal = self._rng_tracker.advance_rng(10) % 255
        base_steal_chance = self.monster.steal['base_chance']
        steal_chance = base_steal_chance // (2 ** self.successful_steals)
        if steal_chance > rng_steal:
            rng_rarity = self._rng_tracker.advance_rng(11) & 255
            if rng_rarity < 32:
                return self.monster.steal[Rarity.RARE]
            else:
                return self.monster.steal[Rarity.COMMON]
        else:
            return None


@dataclass
class Kill(Event):
    monster: Monster
    killer: Character
    overkill: bool = False
    item_1: Optional[ItemDrop] = field(init=False, repr=False)
    item_2: Optional[ItemDrop] = field(init=False, repr=False)
    equipment: Optional[EquipmentDrop] = field(init=False, repr=False)
    equipment_index: Optional[int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.item_1 = self._get_item_1()
        self.item_2 = self._get_item_2()
        self.equipment = self._get_equipment()
        self.equipment_index = self._get_equipment_index()

    def __str__(self) -> str:
        string = f'{self.monster.name} drops: '
        drops = []
        if self.item_1:
            drops.append(str(self.item_1))
        if self.item_2:
            drops.append(str(self.item_2))
        if self.equipment:
            drops.append(f'Equipment #{self.equipment_index} '
                         f'{str(self.equipment)}')
        if len(drops):
            string += ', '.join(drops)
        else:
            string += 'No drops'
        return string

    def _get_item_1(self) -> Optional[ItemDrop]:
        rng_drop = self._rng_tracker.advance_rng(10) % 255
        if self.overkill:
            drop_type = 'overkill'
        else:
            drop_type = 'normal'
        if self.monster.item_1['drop_chance'] > rng_drop:
            rng_rarity = self._rng_tracker.advance_rng(11) & 255
            if rng_rarity < 32:
                return self.monster.item_1[drop_type][Rarity.RARE]
            else:
                return self.monster.item_1[drop_type][Rarity.COMMON]

    def _get_item_2(self) -> Optional[ItemDrop]:
        rng_drop = self._rng_tracker.advance_rng(10) % 255
        if self.overkill:
            drop_type = 'overkill'
        else:
            drop_type = 'normal'
        if self.monster.item_2['drop_chance'] > rng_drop:
            rng_rarity = self._rng_tracker.advance_rng(11) & 255
            if rng_rarity < 32:
                return self.monster.item_2[drop_type][Rarity.RARE]
            else:
                return self.monster.item_2[drop_type][Rarity.COMMON]

    def _get_equipment(self) -> Optional[EquipmentDrop]:
        """Returns equipment obtained from killing a monster
        at the current rng position and advances rng accordingly.
        """
        rng_equipment_drop = self._rng_tracker.advance_rng(10) % 255
        if self.monster.equipment['drop_chance'] <= rng_equipment_drop:
            return

        characters_enabled = [CHARACTERS['tidus'], CHARACTERS['auron']]
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, ChangeParty):
                characters_enabled = event.party_formation
                break

        equipment_owner_base = len(characters_enabled)

        rng_equipment_owner = self._rng_tracker.advance_rng(12)

        # check if killing with a party member
        # always gives the equipment to that character
        killer_is_owner_test = rng_equipment_owner % (equipment_owner_base + 3)
        if killer_is_owner_test >= equipment_owner_base:
            killer_is_owner = True
        else:
            killer_is_owner = False

        # if the killer is a party member (0-6)
        # it gives them a bonus chance for the equipment to be theirs
        if self.killer.index < 7:
            owner = self.killer
            equipment_owner_base += 3

        rng_equipment_owner = rng_equipment_owner % equipment_owner_base
        number_of_enabled_party_members = 0

        # get equipment owner
        characters = tuple(CHARACTERS.values())[:7]
        for character in characters:
            if character in characters_enabled:
                number_of_enabled_party_members += 1
                if rng_equipment_owner < number_of_enabled_party_members:
                    owner = character
                    break

        # get equipment type
        rng_weapon_or_armor = self._rng_tracker.advance_rng(12) & 1
        if rng_weapon_or_armor == 0:
            type_ = EquipmentType.WEAPON
        else:
            type_ = EquipmentType.ARMOR

        # get number of slots
        rng_number_of_slots = self._rng_tracker.advance_rng(12) & 7
        slots_mod = (self.monster.equipment['slots_modifier']
                     + rng_number_of_slots
                     - 4)
        number_of_slots = (slots_mod + ((slots_mod >> 31) & 3)) >> 2
        if number_of_slots > EquipmentSlots.MAX:
            number_of_slots = EquipmentSlots.MAX.value
        elif number_of_slots < EquipmentSlots.MIN:
            number_of_slots = EquipmentSlots.MIN.value

        # get number of abilities
        rng_number_of_abilities = self._rng_tracker.advance_rng(12) & 7
        abilities_mod = (self.monster.equipment['max_ability_rolls_modifier']
                         + rng_number_of_abilities
                         - 4)
        number_of_abilities = ((abilities_mod + ((abilities_mod >> 31) & 7))
                               >> 3)

        ability_arrays = self.monster.equipment['ability_arrays']
        ability_array = ability_arrays[owner.name][type_]

        abilities = []

        # the first ability of the array is usually None, but for kimahri's
        # and auron's weapons and for drops from specific enemies it exists
        forced_ability = ability_array[0]
        if number_of_slots != 0 and forced_ability:
            abilities.append(forced_ability)

        for _ in range(number_of_abilities):
            # if all the slots are filled break
            if len(abilities) >= number_of_slots:
                break
            rng_ability_index = self._rng_tracker.advance_rng(13) % 7 + 1
            ability = ability_array[rng_ability_index]
            # if the ability is not null and not a duplicate add it
            if ability and ability not in abilities:
                abilities.append(ability)

        # other equipment information
        base_weapon_damage = self.monster.equipment['base_weapon_damage']
        bonus_crit = self.monster.equipment['bonus_critical_chance']

        equipment = Equipment(
            owner=owner,
            type_=type_,
            slots=number_of_slots,
            abilities=tuple(abilities),
            base_weapon_damage=base_weapon_damage,
            bonus_crit=bonus_crit,
        )
        equipment_drop = EquipmentDrop(
            equipment=equipment,
            killer=self.killer,
            monster=self.monster,
            killer_is_owner=killer_is_owner,
        )

        return equipment_drop

    def _get_equipment_index(self) -> Optional[int]:
        if not self.equipment:
            return None
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, Kill):
                if event.equipment:
                    return event.equipment_index + 1
        return 1


@dataclass
class Bribe(Kill):

    def _get_item_1(self) -> Optional[ItemDrop]:
        return self.monster.bribe['item']

    def _get_item_2(self) -> None:
        return


@dataclass
class Death(Event):
    dead_character: Character

    def __post_init__(self) -> None:
        self._advance_rng()
        if self.dead_character == CHARACTERS['yojimbo']:
            self._update_compatibility()

    def __str__(self) -> str:
        return f'Character death: {self.dead_character}'

    def _advance_rng(self) -> None:
        for _ in range(3):
            self._rng_tracker.advance_rng(10)

    def _update_compatibility(self) -> None:
        compatibility = self._rng_tracker.compatibility
        self._rng_tracker.compatibility = max(compatibility - 10, 0)


@dataclass
class AdvanceRNG(Event):
    rng_index: int
    number_of_times: int

    def __post_init__(self) -> None:
        self._advance_rng()

    def __str__(self) -> str:
        return f'Advanced rng{self.rng_index} {self.number_of_times} times'

    def _advance_rng(self) -> None:
        for _ in range(self.number_of_times):
            self._rng_tracker.advance_rng(self.rng_index)


@dataclass
class Encounter(Event):
    name: str
    initiative: bool
    forced_condition: Optional[EncounterCondition] = None
    formation: Formation = field(init=False, repr=False)
    condition: EncounterCondition = field(init=False, repr=False)
    index: int = field(init=False, repr=False)
    icvs: Dict[Character, int] = field(
        default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.formation = self._get_formation()
        self.condition = self._get_condition()
        self.index = self._get_index()
        self.icvs = self._get_icvs()

    def __str__(self) -> str:
        if self.condition == EncounterCondition.NORMAL:
            condition = ''
        else:
            condition = f' {self.condition}'
        formation = '+'.join([str(m) for m in self.formation])
        string = (f'Encounter {self.index:3}: {self.name} '
                  f'({formation}){condition}')
        return string

    def _get_index(self) -> int:
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, Encounter):
                return event.index + 1
        return 1

    def _get_formation(self) -> Formation:
        return FORMATIONS.set_formation[self.name]

    def _get_condition(self) -> EncounterCondition:
        condition_rng = self._rng_tracker.advance_rng(1) & 255
        if self.forced_condition:
            return self.forced_condition
        if self.initiative:
            condition_rng -= 33
        if condition_rng < 32:
            return EncounterCondition.PREEMPTIVE
        elif condition_rng < 255 - 32:
            return EncounterCondition.NORMAL
        else:
            return EncounterCondition.AMBUSH

    def _get_icvs(self) -> Dict[Character, int]:
        icvs = {}
        if self.condition is EncounterCondition.PREEMPTIVE:
            for c in CHARACTERS.values():
                icvs[c.name] = 0
        elif self.condition is EncounterCondition.AMBUSH:
            for c in CHARACTERS.values():
                icvs[c.name] = ICV_BASE[c.stats[Stat.AGILITY]] * 3
        else:
            for c in CHARACTERS.values():
                base = ICV_BASE[c.stats[Stat.AGILITY]] * 3
                index = c.index + 20 if c.index < 7 else 27
                variance_rng = self._rng_tracker.advance_rng(index)
                variance = ICV_VARIANCE[c.stats[Stat.AGILITY]] + 1
                variance = variance_rng % variance
                icvs[c.name] = base - variance
        return icvs


@dataclass
class SimulatedEncounter(Encounter):

    def _get_index(self) -> int:
        # simulated encounter don't increment the game's
        # encounter count used to calculate aeons' stats
        return super()._get_index() - 1

    def _get_formation(self) -> Formation:
        return FORMATIONS.simulated[self.name]


@dataclass
class RandomEncounter(Encounter):
    zone: str = field(init=False, repr=False)
    random_index: int = field(init=False, repr=False)
    zone_index: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.zone = self.name
        super().__post_init__()
        self.random_index = self._get_random_index()
        self.zone_index = self._get_zone_index()

    def __str__(self) -> str:
        if self.condition == EncounterCondition.NORMAL:
            condition = ''
        else:
            condition = f' {self.condition}'
        formation = ', '.join([str(m) for m in self.formation])
        string = (f'Encounter {self.index:3}|{self.random_index:3}|'
                  f'{self.zone_index:3}| {self.zone}: {formation}{condition}')
        return string

    def _get_formation(self) -> Formation:
        rng_value = self._rng_tracker.advance_rng(1)
        zone_formations = FORMATIONS.random[self.zone]
        formation_index = rng_value % len(zone_formations)
        return zone_formations[formation_index]

    def _get_random_index(self) -> int:
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, RandomEncounter):
                return event.random_index + 1
        return 1

    def _get_zone_index(self) -> int:
        for event in reversed(self._rng_tracker.events_sequence):
            if isinstance(event, RandomEncounter):
                if event.zone == self.zone:
                    return event.zone_index + 1
        return 1

    def _get_name(self) -> str:
        return f'{self.zone} [{self.zone_index}]'


@dataclass
class MultizoneRandomEncounter(RandomEncounter):

    def __str__(self) -> str:
        if self.condition == EncounterCondition.NORMAL:
            condition = ''
        else:
            condition = f' {self.condition}'
        formations = []
        for f in self.formation:
            formations.append(f'[{", ".join([str(m) for m in f])}]')
        formations = '/'.join(formations)
        string = (f'Encounter {self.index:3}|{self.random_index:3}|'
                  f'{self.zone_index:3}| {self.zone}: {formations}{condition}')
        return string

    def _get_formation(self) -> List[Formation]:
        rng_value = self._rng_tracker.advance_rng(1)
        formations = []
        for zone in self.zone.split('/'):
            zone_formations = FORMATIONS.random[zone]
            formation_index = rng_value % len(zone_formations)
            formations.append(zone_formations[formation_index])
        return formations


@dataclass
class CharacterAction(Event):
    character: Character
    action: Action
    target: Union[Character, Monster]
    hit: bool = field(init=False, repr=False)
    damage: int = field(init=False, repr=False)
    damage_rng: int = field(init=False, repr=False)
    crit: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.hit = self._get_hit()
        self.damage, self.damage_rng, self.crit = self._get_damage()

    def __str__(self) -> str:
        string = (f'{self.character.name} -> {self.action.name}'
                  f' -> {self.target.name}:')
        if self.hit:
            if self.action.does_damage:
                string += f' [{self.damage_rng}/31]'
                string += f' {self.damage}'
                if self.crit:
                    string += ' (Crit)'
            else:
                string += ' (No damage)'
        else:
            string += ' Miss'
        return string

    def _get_hit(self) -> bool:
        if not self.action.can_miss:
            return True
        index = min(36 + self.character.index, 43)
        hit_rng = self._rng_tracker.advance_rng(index) % 101
        luck = self.character.stats[Stat.LUCK]
        accuracy = self.character.stats[Stat.ACCURACY]
        target_evasion = self.target.stats[Stat.EVASION]
        target_luck = max(self.target.stats[Stat.LUCK], 1)
        # unused for now
        aims = 0
        target_reflexes = 0
        hit_chance = accuracy * 2
        hit_chance = (hit_chance * 0x66666667) // 0xffffffff
        hit_chance = hit_chance // 2
        hit_chance_index = hit_chance // 0x80000000
        hit_chance_index += hit_chance - target_evasion + 10
        if hit_chance_index < 0:
            hit_chance_index = 0
        elif hit_chance_index > 8:
            hit_chance_index = 8
        hit_chance = HIT_CHANCE_TABLE[hit_chance_index] + luck
        hit_chance += (aims - target_reflexes) * 10 - target_luck
        return hit_chance > hit_rng

    def _get_crit(self) -> bool:
        if not self.action.can_crit:
            return False
        index = min(20 + self.character.index, 27)
        crit_roll = self._rng_tracker.advance_rng(index) % 101
        luck = self.character.stats[Stat.LUCK]
        target_luck = max(self.target.stats[Stat.LUCK], 1)
        crit_chance = luck - target_luck
        if self.action.uses_bonus_crit:
            crit_chance += self.character.stats[Stat.BONUS_CRIT]
        return crit_roll < crit_chance

    def _get_damage(self) -> Tuple[int, int, bool]:
        if not self.hit or not self.action.does_damage:
            return 0, 0, False
        index = min(20 + self.character.index, 27)
        damage_rng = self._rng_tracker.advance_rng(index) & 31
        variance = damage_rng + 0xf0
        crit = self._get_crit()
        damage_type = self.action.damage_type
        if self.action.element:
            affinity = self.target.elemental_affinities[self.action.element]
            if affinity == ElementalAffinity.WEAK:
                element_mod = 1.5
            elif affinity == ElementalAffinity.RESISTS:
                element_mod = 0.5
            elif affinity == ElementalAffinity.IMMUNE:
                element_mod = 0
            else:
                element_mod = 1
        else:
            element_mod = 1

        # special cases where the damage formula
        # is a lot less complicated
        if damage_type == DamageType.ITEM:
            damage = self.action.base_damage * 50
            damage = damage * variance // 256
            if crit:
                damage = damage * 2
            damage = int(damage * element_mod)
            return damage, damage_rng, crit
        elif damage_type == DamageType.FIXED:
            damage = self.action.base_damage
            return damage, damage_rng, crit
        elif damage_type == DamageType.PERCENTAGE:
            damage = f'{self.action.base_damage}%'
            return damage, damage_rng, crit
        elif damage_type == DamageType.HP:
            damage = self.character.stats[Stat.HP]
            damage = damage * self.action.base_damage // 100
            if crit:
                damage = int(damage * 2)
            return damage, damage_rng, crit
        elif damage_type == DamageType.GIL:
            damage = 0  # damage = gil/10
            return damage, damage_rng, crit

        # not many relevant instances of cheers or focuses on enemies
        # not used for now
        target_cheers = 0
        target_focuses = 0
        cheers = self.character.stats[Stat.CHEER]
        focuses = self.character.stats[Stat.FOCUS]
        if damage_type == DamageType.STRENGTH:
            if self.action.base_damage:
                base_damage = self.action.base_damage
            else:
                base_damage = self.character.stats[Stat.WEAPON_DAMAGE]
            defensive_buffs = target_cheers
            offensive_buffs = cheers
            offensive_stat = self.character.stats[Stat.STRENGTH]
            bonus = self.character.stats[Stat.BONUS_STRENGTH]
            defensive_stat = max(self.target.stats[Stat.DEFENSE], 1)
        elif damage_type in (DamageType.MAGIC, DamageType.SPECIAL_MAGIC,
                             DamageType.HEALING):
            base_damage = self.action.base_damage
            defensive_buffs = target_focuses
            offensive_buffs = focuses
            offensive_stat = self.character.stats[Stat.MAGIC]
            bonus = self.character.stats[Stat.BONUS_MAGIC]
            if self.action.damage_type == DamageType.MAGIC:
                defensive_stat = max(self.target.stats[Stat.MAGIC_DEFENSE], 1)
            else:
                defensive_stat = 0

        offensive_stat += offensive_buffs

        if damage_type in (DamageType.STRENGTH, DamageType.SPECIAL_MAGIC):
            power = offensive_stat * offensive_stat * offensive_stat
            power = (power // 0x20) + 0x1e
        elif damage_type == DamageType.MAGIC:
            power = offensive_stat * offensive_stat
            power = (power * 0x2AAAAAAB) // 0xffffffff
            power = power + (power // 0x80000000)
            power = (power + base_damage) * base_damage
            power = power // 4

        mitigation_1 = defensive_stat * defensive_stat
        mitigation_1 = (mitigation_1 * 0x2E8BA2E9) // 0xffffffff
        mitigation_1 = mitigation_1 // 2
        mitigation_1 = mitigation_1 + (mitigation_1 // 0x80000000)
        mitigation_2 = defensive_stat * 0x33
        mitigation = mitigation_2 - mitigation_1
        mitigation = (mitigation * 0x66666667) // 0xffffffff
        mitigation = mitigation // 4
        mitigation = mitigation + (mitigation // 0x80000000)
        mitigation = 0x2da - mitigation

        damage_1 = power * mitigation
        damage_2 = (damage_1 * -1282606671) // 0xffffffff
        damage_3 = damage_2 + damage_1
        damage_3 = damage_3 // 0x200
        damage_3 = damage_3 * (15 - defensive_buffs)
        damage_4 = (damage_3 * -2004318071) // 0xffffffff
        damage = (damage_4 + damage_3) // 0x8
        damage = damage + (damage // 0x80000000)
        if damage_type in (DamageType.STRENGTH, DamageType.SPECIAL_MAGIC):
            damage = damage * base_damage // 0x10
        damage = damage * variance // 0x100

        if crit:
            damage = damage * 2

        damage = damage * element_mod

        if (damage_type == DamageType.STRENGTH
                and isinstance(self.target, Monster)
                and self.target.armored
                and not self.character.stats[Stat.PIERCING]):
            damage = damage // 3

        damage = damage + (damage * bonus // 100)

        damage = int(damage)

        return damage, damage_rng, crit


@dataclass
class ChangeStat(Event):
    character: Character
    stat: Stat
    stat_value: int

    def __post_init__(self) -> None:
        self.stat_value = self._set_stat()

    def __str__(self) -> str:
        return (f'{self.character.name}\'s {self.stat} '
                f'changed to {self.stat_value}')

    def _set_stat(self) -> int:
        self.character.set_stat(self.stat, self.stat_value)
        return self.character.stats[self.stat]


@dataclass
class Escape(Event):
    character: Character
    escape: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.escape = self._get_escape()

    def __str__(self) -> str:
        string = f'{self.character.name}: Escape ->'
        if self.escape:
            string += ' Succeeded'
        else:
            string += ' Failed'
        return string

    def _get_escape(self) -> bool:
        index = 20 + self.character.index
        escape_roll = self._rng_tracker.advance_rng(index) & 255
        return escape_roll < 191


@dataclass
class Comment(Event):
    text: str

    def __str__(self) -> str:
        return self.text


@dataclass
class YojimboTurn(Event):
    action: YojimboAction
    monster: Monster
    overdrive: bool = False
    is_attack_free: bool = field(init=False, repr=False)
    gil: int = field(init=False, repr=False)
    compatibility: int = field(init=False, repr=False)
    motivation: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.is_attack_free = self._free_attack_check()
        if self.is_attack_free:
            self.gil = 0
            self.action, self.motivation = self._get_free_attack()
        elif self.action.needed_motivation is not None:
            self.gil, self.motivation = self._get_gil()
        else:
            self.gil = 0
            self.motivation = 0
        self.compatibility = self._update_compatibility()

    def __str__(self) -> str:
        if self.is_attack_free:
            cost = 'free'
        else:
            cost = f'{self.gil} gil'
        string = (f'{self.action.name} -> {self.monster}: '
                  f'{cost} [{self.motivation}/{self.action.needed_motivation}'
                  f' motivation][{self.compatibility}/255 compatibility]')
        return string

    def _free_attack_check(self) -> bool:
        rng = self._rng_tracker.advance_rng(17) & 255
        compatibility = self._rng_tracker.compatibility // 4
        return compatibility > rng

    def _get_free_attack(self) -> Tuple[YojimboAction, int]:
        base_motivation = self._rng_tracker.compatibility // 4
        rng = self._rng_tracker.advance_rng(17) & 0x3f
        motivation = base_motivation + rng
        attacks = [a for a in YOJIMBO_ACTIONS.values()
                   if a.needed_motivation is not None]
        attacks.sort(key=lambda a: a.needed_motivation)
        for a in attacks:
            if motivation >= a.needed_motivation:
                attack = a

        if (attack == YOJIMBO_ACTIONS['zanmato']
                and self.monster.zanmato_level > 0):
            attack = YOJIMBO_ACTIONS['wakizashi_mt']
        return attack, motivation

    def _get_gil(self) -> Tuple[int, int]:
        """"""
        base_motivation = (self._rng_tracker.compatibility
                           // COMPATIBILITY_MODIFIER)
        zanmato_resistance = ZANMATO_LEVELS[self.monster.zanmato_level]
        rng_motivation = self._rng_tracker.advance_rng(17) & 0x3f
        # the zanmato level of the monster is only used to check for zanmato
        # if the desired attack is not zanmato then a second calculation is
        # made using the lowest zanmato level
        if (self.action != YOJIMBO_ACTIONS['zanmato']
                and self.monster.zanmato_level > 0):
            zanmato_resistance = ZANMATO_LEVELS[0]
            rng_motivation = self._rng_tracker.advance_rng(17) & 0x3f
        fixed_motivation = int(base_motivation * zanmato_resistance)
        fixed_motivation += rng_motivation
        if self.overdrive:
            fixed_motivation += OVERDRIVE_MOTIVATION

        motivation = fixed_motivation
        gil = 1
        while motivation < self.action.needed_motivation:
            gil = gil * 2
            gil_motivation = self.gil_to_motivation(gil)
            gil_motivation = int(gil_motivation * zanmato_resistance)
            motivation = fixed_motivation + gil_motivation
        return gil, motivation

    def _update_compatibility(self) -> int:
        modifier = self.action.compatibility_modifier
        self._rng_tracker.compatibility += modifier
        return self._rng_tracker.compatibility

    @staticmethod
    def gil_to_motivation(gil: int) -> int:
        motivation = int(math.log(gil, 2))
        if Configs.ps2:
            motivation = (motivation - 1) * 2
        else:
            motivation = (motivation - 2) * 4
        return max(motivation, 0)
