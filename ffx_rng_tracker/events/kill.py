from dataclasses import dataclass, field

from ..data.constants import (Character, EquipmentSlots, EquipmentType,
                              KillType, Rarity)
from ..data.equipment import Equipment, EquipmentDrop
from ..data.items import ItemDrop
from ..data.monsters import Monster
from .main import Event


@dataclass
class Kill(Event):
    monster: Monster
    killer: Character
    ap_credited_characters: list[Character] = field(default_factory=list)
    kill_type: KillType = KillType.NORMAL

    def __post_init__(self) -> None:
        self.item_1 = self._get_item_1()
        if self.item_1:
            self.gamestate.add_to_inventory(
                self.item_1.item, self.item_1.quantity)
        self.item_2 = self._get_item_2()
        if self.item_2:
            self.gamestate.add_to_inventory(
                self.item_2.item, self.item_2.quantity)
        self.gamestate.gil += self.monster.gil
        rng_current_positions = self.gamestate._rng_tracker._rng_current_positions
        self.ability_rolls = rng_current_positions[13]
        self.equipment = self._get_equipment()
        self.ability_rolls = rng_current_positions[13] - self.ability_rolls
        if self.equipment:
            self.gamestate.add_to_equipment_inventory(self.equipment.equipment)
        self.equipment_index = self._get_equipment_index()
        self._give_ap()

    def _give_ap(self):
        ap = self.monster.ap[self.kill_type]
        for character in self.ap_credited_characters:
            self.gamestate.characters[character].ap += ap

    def __str__(self) -> str:
        string = f'Drops: {self.monster} | '
        if self.item_1 and self.item_2:
            string += f'{self.item_1}, {self.item_2}'
        elif self.item_1:
            string += f'{self.item_1}'
        elif self.item_2:
            string += f'{self.item_2}'
        else:
            string += '-'
        string += f' | {self.monster.ap[self.kill_type]} AP'
        if self.ap_credited_characters:
            string += f' to {''.join(c[0] for c in self.ap_credited_characters)}'
        if self.kill_type is KillType.OVERKILL:
            string += ' (OK)'
        if self.equipment:
            string += (f' | Equipment #{self.equipment_index} '
                       f'{str(self.equipment)}'
                       f'({self.ability_rolls} ability roll'
                       f'{'s' * (self.ability_rolls != 1)})'
                       )
        return string

    def _get_item_1(self) -> ItemDrop | None:
        rng_drop = self._advance_rng(10) % 255
        if self.monster.item_1.drop_chance > rng_drop:
            rng_rarity = self._advance_rng(11) & 255
            if rng_rarity < 32:
                return self.monster.item_1.items[self.kill_type, Rarity.RARE]
            else:
                return self.monster.item_1.items[self.kill_type, Rarity.COMMON]

    def _get_item_2(self) -> ItemDrop | None:
        rng_drop = self._advance_rng(10) % 255
        if self.monster.item_2.drop_chance > rng_drop:
            rng_rarity = self._advance_rng(11) & 255
            if rng_rarity < 32:
                return self.monster.item_2.items[self.kill_type, Rarity.RARE]
            else:
                return self.monster.item_2.items[self.kill_type, Rarity.COMMON]

    def _get_equipment(self) -> EquipmentDrop | None:
        """Returns equipment obtained from killing a monster
        at the current rng position and advances rng accordingly.
        """
        rng_equipment_drop = self._advance_rng(10) % 255
        if self.monster.equipment.drop_chance <= rng_equipment_drop:
            return

        possible_owners = [c for c in tuple(Character)[:7]
                           if c in self.gamestate.party]
        rng_equipment_owner = self._advance_rng(12)

        # check if killing with a party member
        # always gives the equipment to that character
        killer_is_owner_test = rng_equipment_owner % (len(possible_owners) + 3)
        if killer_is_owner_test >= len(possible_owners):
            killer_is_owner = True
        else:
            killer_is_owner = False

        # if the killer is a party member (0-6)
        # it gives them a bonus chance for the equipment to be theirs
        if tuple(Character).index(self.killer) < 7:
            for _ in range(3):
                possible_owners.append(self.killer)

        rng_equipment_owner = rng_equipment_owner % len(possible_owners)
        owner = possible_owners[rng_equipment_owner]

        rng_weapon_or_armor = self._advance_rng(12) & 1
        if rng_weapon_or_armor == 0:
            type_ = EquipmentType.WEAPON
        else:
            type_ = EquipmentType.ARMOR

        rng_number_of_slots = self._advance_rng(12) & 7
        number_of_slots = self.monster.equipment.slots_range[rng_number_of_slots]
        if number_of_slots > EquipmentSlots.MAX:
            number_of_slots = EquipmentSlots.MAX.value
        elif number_of_slots < EquipmentSlots.MIN:
            number_of_slots = EquipmentSlots.MIN.value

        # get number of abilities
        rng_number_of_abilities = self._advance_rng(12) & 7
        number_of_abilities = self.monster.equipment.max_ability_rolls_range[rng_number_of_abilities]

        abilities_list = self.monster.equipment.ability_lists[owner, type_]

        abilities = []

        forced_ability = abilities_list[0]
        if forced_ability:
            abilities.append(forced_ability)

        for _ in range(number_of_abilities):
            # if all the slots are filled break
            if len(abilities) >= number_of_slots:
                break
            rng_ability_index = self._advance_rng(13) % 7 + 1
            ability = abilities_list[rng_ability_index]
            # if the ability is not null and not a duplicate add it
            if ability and ability not in abilities:
                abilities.append(ability)

        # other equipment information
        base_weapon_damage = self.monster.equipment.base_weapon_damage
        bonus_crit = self.monster.equipment.bonus_critical_chance

        equipment = Equipment(
            owner=owner,
            type_=type_,
            slots=number_of_slots,
            abilities=abilities,
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

    def _get_equipment_index(self) -> int | None:
        if not self.equipment:
            return None
        self.gamestate.equipment_drops += 1
        return self.gamestate.equipment_drops


@dataclass
class Bribe(Kill):

    def __post_init__(self) -> None:
        self.kill_type = KillType.NORMAL
        super().__post_init__()

    def _get_item_1(self) -> ItemDrop | None:
        return self.monster.bribe.item

    def _get_item_2(self) -> None:
        return
