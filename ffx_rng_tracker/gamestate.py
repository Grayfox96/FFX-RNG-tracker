from itertools import chain

from .configs import Configs
from .data.actions import Action
from .data.actor import Actor, CharacterActor, MonsterActor
from .data.characters import CHARACTERS_DEFAULTS, calculate_power_base
from .data.constants import (AEONS_STATS_CONSTANTS, BASE_COMPATIBILITY,
                             ENCOUNTERS_YUNA_STATS, Character, Item, Stat,
                             Status)
from .data.equipment import Equipment
from .data.items import Inventory
from .data.statuses import DURATION_STATUSES, TEMPORARY_STATUSES
from .tracker import FFXRNGTracker


class GameState:
    """Keeps track of various state variables necessary
    to properly instantiate events.
    """

    def __init__(self, rng_tracker: FFXRNGTracker) -> None:
        self._rng_tracker = rng_tracker
        self._default_party = Character.TIDUS, Character.AURON
        self.characters = self._get_characters()
        self.zone_encounters_counts: dict[str, int] = {}
        self.inventory = Inventory()
        self.equipment_inventory: list[Equipment | None] = []
        self.party: list[Character] = []
        self.monster_party: list[MonsterActor] = []
        self.reset()

    def _get_characters(self) -> dict[Character, CharacterActor]:
        characters = {}
        for character, defaults in CHARACTERS_DEFAULTS.items():
            characters[character] = CharacterActor(defaults)
        return characters

    def get_min_ctb(self) -> int:
        ctbs = set()
        actors = [self.characters[c] for c in self.party] + self.monster_party
        for actor in actors:
            if (Status.DEATH in actor.statuses
                    or Status.EJECT in actor.statuses):
                continue
            ctbs.add(actor.ctb)
        if not ctbs:
            # TODO
            # should this raise an error?
            return 0
        return min(ctbs)

    def normalize_ctbs(self, min_ctb: int) -> None:
        if min_ctb == 0:
            return
        for actor in chain(self.characters.values(), self.monster_party):
            actor.ctb -= min_ctb

    def setup_autostatuses(self) -> None:
        for actor in self.characters.values():
            auto_statuses = set(actor.auto_statuses)
            if actor.in_crit:
                auto_statuses.update(actor.sos_auto_statuses)
            for status in auto_statuses:
                if status not in actor.statuses:
                    actor.statuses[status] = 255
        for actor in self.monster_party:
            for status in actor.monster.auto_statuses:
                if status not in actor.statuses:
                    actor.statuses[status] = 255

    def calculate_aeon_stats(self) -> None:
        yuna_stats = self.characters[Character.YUNA].stats.copy()
        yuna_stats[Stat.HP] = min(yuna_stats[Stat.HP], 9999)
        yuna_stats[Stat.MP] = min(yuna_stats[Stat.MP], 999)
        enc_tier = min(max(0, (self.encounters_count - 30) // 30), 19)

        check = tuple([enc_tier] + [v for v in yuna_stats.values()])
        if self.calculate_aeon_stats_cache == check:
            return
        self.calculate_aeon_stats_cache = check

        power_base = calculate_power_base(yuna_stats)

        enc_stats = {stat: ENCOUNTERS_YUNA_STATS[stat][enc_tier]
                     for stat in yuna_stats}
        enc_power_base = calculate_power_base(enc_stats)

        # TODO
        # add bonus aeon stats to gamestate
        bonus_stats: dict[Stat, int] = {}

        for aeon, stats_constants in AEONS_STATS_CONSTANTS.items():
            aeon = self.characters[aeon]
            aeon.set_stat(Stat.LUCK, yuna_stats[Stat.LUCK])
            for stat, (x, y) in stats_constants.items():
                value = (yuna_stats[stat] * x // 100) + int(power_base * y)
                enc_value = (enc_stats[stat] * x // 100) + int(enc_power_base * y)
                value = max(value, enc_value) + bonus_stats.get(stat, 0)
                aeon.set_stat(stat, value)

    def process_start_of_turn(self, actor: Actor) -> None:
        for status in TEMPORARY_STATUSES:
            actor.statuses.pop(status, None)
        self.setup_autostatuses()

    def process_end_of_turn(self, actor: Actor, action: Action) -> None:
        self.last_actor = actor
        self.last_actor.last_action = action
        if action.destroys_user:
            actor.statuses[Status.EJECT] = 254
        statuses = actor.statuses.copy()
        for status, stacks in statuses.items():
            if status is Status.POISON:
                actor.current_hp -= actor.max_hp // 4
            if stacks >= 254:
                continue
            if status not in DURATION_STATUSES:
                continue
            stacks -= 1
            if stacks <= 0:
                if status is Status.DOOM:
                    actor.statuses[Status.DEATH] = 254
                actor.statuses.pop(status, None)
            else:
                actor.statuses[status] = stacks
        actors = chain(self.characters.values(), self.monster_party)
        ctb_ticks = self.get_min_ctb()
        self.normalize_ctbs(ctb_ticks)
        actors_with_regen = [a for a in actors if Status.REGEN in a.statuses]
        for actor in actors_with_regen:
            actor.current_hp += (ctb_ticks * (actor.max_hp // 256)) + 100

    def process_start_of_encounter(self) -> None:
        # TODO
        # this makes endencounter optional for most situations
        # calling the end method twice causes no problems for now but
        # calling start and end separately might become mandatory at
        # some point
        self.process_end_of_encounter()

        self.calculate_aeon_stats()

    def process_end_of_encounter(self) -> None:
        for actor in self.characters.values():
            if Status.DEATH in actor.statuses:
                actor.current_hp = 1
            actor.ctb = 0
            actor.statuses.clear()
            actor.buffs.clear()
        self.monster_party.clear()

    def clean_equipment_inventory(self) -> None:
        while (self.equipment_inventory
               and self.equipment_inventory[-1] is None):
            self.equipment_inventory.pop()

    def add_to_equipment_inventory(self, equipment: Equipment) -> None:
        self.clean_equipment_inventory()
        if None in self.equipment_inventory:
            index = self.equipment_inventory.index(None)
            self.equipment_inventory[index] = equipment
        else:
            self.equipment_inventory.append(equipment)

    def reset(self) -> None:
        self._rng_tracker.reset()
        self.inventory.reset()
        self.inventory.add(Item.POTION, 10)
        self.inventory.add(Item.PHOENIX_DOWN, 3)
        self.equipment_inventory.clear()
        self.gil = 300
        self.party.clear()
        self.party.extend(self._default_party)
        self.monster_party.clear()
        self.last_actor: Actor = self.characters[Character.TIDUS]
        self.compatibility = BASE_COMPATIBILITY[Configs.game_version]
        self.equipment_drops = 0
        self.encounters_count = 0
        self.random_encounters_count = 0
        self.zone_encounters_counts.clear()
        self.live_distance = 0
        for actor in self.characters.values():
            actor.reset()
        self.calculate_aeon_stats_cache = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.calculate_aeon_stats()
        for actor in self.characters.values():
            if actor.index > 7:
                actor.current_hp = 99999
                actor.current_mp = 9999

    @property
    def gil(self) -> int:
        return self._gil

    @gil.setter
    def gil(self, value: int) -> None:
        value = min(max(0, value), 999999999)
        self._gil = value

    @property
    def compatibility(self) -> int:
        return self._compatibility

    @compatibility.setter
    def compatibility(self, value: int) -> None:
        self._compatibility = min(max(0, value), 255)

    @property
    def seed(self) -> int:
        return self._rng_tracker.seed

    @seed.setter
    def seed(self, seed: int) -> None:
        self._rng_tracker.__init__(seed)
