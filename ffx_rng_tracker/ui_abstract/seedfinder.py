from dataclasses import dataclass
from itertools import product

from ..configs import Configs
from ..data.constants import DamageFormula
from ..data.seeds import (DAMAGE_VALUES_NEEDED, FRAMES_FROM_BOOT,
                          POSSIBLE_XORED_DATETIMES, datetime_to_seed)
from ..events.character_action import CharacterAction
from .actions_tracker import ActionsTracker


@dataclass
class SeedFinder(ActionsTracker):

    def get_default_input_data(self) -> str:
        input_data = ('encounter\nauron attack sinscale_6\n'
                      'tidus attack sinscale_6\nauron attack sinscale_6'
                      )
        return input_data

    def find_seed(self) -> None:
        # first 2 lines are always input dvs and "///"
        input_dvs, _, *input_lines = self.input_widget.get_input().splitlines()
        input_text = '\n'.join(input_lines)
        edited_input_text = self.edit_input(input_text)
        events = self.parser.parse(edited_input_text)

        indexes = []
        for index, event in enumerate(events):
            if (isinstance(event, CharacterAction)
                    and event.action.damage_formula is not DamageFormula.NO_DAMAGE
                    and event.action.damages_hp):
                indexes.append(index)

        damage_values_needed = DAMAGE_VALUES_NEEDED[Configs.game_version]
        if len(indexes) < damage_values_needed:
            self.warning_popup.print_output(
                f'Need {damage_values_needed} damaging actions.')
            return

        for symbol in (',', '-', '/', '\\', '.'):
            input_dvs = input_dvs.replace(symbol, ' ')
        input_dvs = input_dvs.split()
        try:
            input_dvs = [int(i) for i in input_dvs]
        except ValueError as error:
            error = str(error).split(':', 1)[1]
            self.warning_popup.print_output(
                f'{error} is not a valid damage value.')
            return

        if len(input_dvs) < len(indexes):
            self.warning_popup.print_output(
                f'Need {len(indexes)} damage values.')
            return

        input_dvs = input_dvs[:len(indexes)]

        damage_values = []
        date_times = POSSIBLE_XORED_DATETIMES[Configs.game_version]
        frames = FRAMES_FROM_BOOT[Configs.game_version]
        already_tested_seeds = set()
        for frame, dt in product(range(frames), date_times):
            seed = datetime_to_seed(dt, frame)
            if seed in already_tested_seeds:
                continue
            already_tested_seeds.add(seed)
            self.parser.gamestate.seed = seed
            self.parser.gamestate.reset()
            events = self.parser.parse(edited_input_text)
            damage_values.clear()
            for index in indexes:
                event: CharacterAction = events[index]
                damage_values.extend(r.hp.damage for r in event.results)
            if damage_values == input_dvs:
                self.input_widget.set_input(
                    f'# Seed number: {seed}\n{input_text}')
                self.warning_popup.print_output(f'Seed: {seed}')
                self.callback()
                break
        else:
            self.warning_popup.print_output('Seed not found!')
