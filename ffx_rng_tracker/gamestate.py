from .configs import Configs
from .data.characters import CHARACTERS_DEFAULTS, CharacterState
from .data.constants import BASE_COMPATIBILITY, Character
from .data.monsters import MONSTERS, MonsterState
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

    def normalize_ctbs(self) -> None:
        ctbs = []
        for c, cs in self.characters.items():
            if c not in self.party or cs.dead or cs.inactive:
                cs.ctb = 0
            else:
                ctbs.append(cs.ctb)
        for m in self.monster_party:
            if m.dead:
                m.ctb = 0
            else:
                ctbs.append(m.ctb)
        if not ctbs:
            return
        min_ctb = min(ctbs)
        for c in self.characters.values():
            c.ctb -= min_ctb
        for m in self.monster_party:
            m.ctb -= min_ctb

    def reset(self) -> None:
        self._rng_tracker.reset()
        self.party = [Character.TIDUS, Character.AURON]
        self.monster_party = [MonsterState(MONSTERS['dummy'])]
        self.last_character = self.characters[Character.TIDUS]
        self.compatibility = BASE_COMPATIBILITY[Configs.game_version]
        self.equipment_drops = 0
        self.encounters_count = 0
        self.random_encounters_count = 0
        self.zone_encounters_counts.clear()
        for character in self.characters.values():
            character.reset()

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
