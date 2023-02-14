from itertools import chain

from .configs import Configs
from .data.characters import CHARACTERS_DEFAULTS, CharacterState
from .data.constants import BASE_COMPATIBILITY, Character, Item, Status
from .data.equipment import Equipment
from .data.items import InventorySlot
from .data.monsters import MonsterState
from .data.statuses import DURATION_STATUSES, TEMPORARY_STATUSES
from .tracker import FFXRNGTracker


class GameState:
    """Keeps track of various state variables necessary
    to properly instantiate events.
    """

    def __init__(self, seed: int) -> None:
        self._rng_tracker = FFXRNGTracker(seed)
        self.characters = self._get_characters()
        self.zone_encounters_counts: dict[str, int] = {}
        self._compatibility = BASE_COMPATIBILITY[Configs.game_version]
        self.reset()

    def __repr__(self) -> str:
        return f'{type(self).__name__}(seed=({self.seed}))'

    def _get_characters(self) -> dict[Character, CharacterState]:
        characters = {}
        for character, defaults in CHARACTERS_DEFAULTS.items():
            characters[character] = CharacterState(defaults)
        return characters

    def get_min_ctb(self) -> int:
        ctbs = set()
        for c, cs in self.characters.items():
            if c not in self.party or cs.dead or cs.inactive:
                cs.ctb = 0
            else:
                ctbs.add(cs.ctb)
        for m in self.monster_party:
            if m.dead:
                m.ctb = 0
            else:
                ctbs.add(m.ctb)
        if not ctbs:
            # TODO
            # should this raise an error?
            return 0
        return min(ctbs)

    def normalize_ctbs(self, min_ctb: int) -> None:
        for actor in chain(self.characters.values(), self.monster_party):
            actor.ctb -= min_ctb

    def setup_autostatuses(self) -> None:
        for character in self.characters.values():
            auto_statuses = set(character.auto_statuses)
            if character.in_crit:
                auto_statuses.update(character.sos_auto_statuses)
            for status in auto_statuses:
                if status not in character.statuses:
                    character.statuses[status] = 255
        for monster in self.monster_party:
            for status in monster.monster.auto_statuses:
                if status not in monster.statuses:
                    monster.statuses[status] = 255

    def process_start_of_turn(self,
                              actor: CharacterState | MonsterState,
                              ) -> None:
        for status in TEMPORARY_STATUSES:
            actor.statuses.pop(status, None)
        self.setup_autostatuses()

    def process_end_of_turn(self,
                            actor: CharacterState | MonsterState,
                            ) -> None:
        self.last_actor = actor
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
            actor.current_hp += (ctb_ticks * actor.max_hp // 256) + 100

    def process_start_of_encounter(self) -> None:
        # TODO
        # this makes endencounter optional for most situations
        # calling the end method twice causes no problems for now but
        # calling start and end separately might become mandatory at
        # some point
        self.process_end_of_encounter()

    def process_end_of_encounter(self) -> None:
        for state in self.characters.values():
            if Status.DEATH in state.statuses:
                state.current_hp = 1
            state.ctb = 0
            state.statuses.clear()
            for buff in state.buffs:
                state.buffs[buff] = 0
        self.monster_party.clear()

    def add_to_inventory(self, item: Item, quantity: int) -> None:
        empty_slot = None
        for slot in self.inventory:
            if not empty_slot and not slot.item:
                empty_slot = slot
            elif slot.item is item:
                slot.quantity += quantity
                return
        empty_slot.item = item
        empty_slot.quantity = quantity

    def reset(self) -> None:
        self._rng_tracker.reset()
        self.inventory = [InventorySlot() for _ in Item]
        self.inventory[0] = InventorySlot(Item.POTION, 10)
        self.inventory[1] = InventorySlot(Item.PHOENIX_DOWN, 3)
        self.equipment_inventory: list[Equipment] = []
        self.gil = 300
        self.party = [Character.TIDUS, Character.AURON]
        self.monster_party: list[MonsterState] = []
        self.last_actor: CharacterState | MonsterState = self.characters[Character.TIDUS]
        self.compatibility = BASE_COMPATIBILITY[Configs.game_version]
        self.equipment_drops = 0
        self.encounters_count = 0
        self.random_encounters_count = 0
        self.zone_encounters_counts.clear()
        for character in self.characters.values():
            character.reset()

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
