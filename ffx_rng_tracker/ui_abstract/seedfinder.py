from dataclasses import dataclass
from itertools import product

from ..configs import Configs
from ..data.seeds import (DAMAGE_VALUES_NEEDED, POSSIBLE_XORED_DATETIMES,
                          datetime_to_seed, get_frames_from_boot)
from ..events.character_action import CharacterAction
from .actions_tracker import ActionsTracker
from .input_widget import InputWidget


@dataclass
class SeedFinder(ActionsTracker):
    damage_values_widget: InputWidget

    def get_default_input_data(self) -> str:
        input_data = ('encounter\nauron attack sinscale_6\n'
                      'tidus attack sinscale_6\nauron attack sinscale_6'
                      )
        return input_data

    def find_seed(self) -> None:
        input_text = self.edit_input(self.input_widget.get_input())
        events = self.parser.parse(input_text)

        indexes = []
        for index, event in enumerate(events):
            if isinstance(event, CharacterAction):
                if event.action.does_damage:
                    indexes.append(index)

        damage_values_needed = DAMAGE_VALUES_NEEDED[Configs.game_version]
        if len(indexes) < damage_values_needed:
            self.warning_popup.print_output(
                f'Need {damage_values_needed} damaging actions.')
            return

        input_dvs = self.damage_values_widget.get_input()
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
        frames = get_frames_from_boot()
        already_tested_seeds = set()
        for frame, dt in product(range(frames), date_times):
            seed = datetime_to_seed(dt, frame)
            if seed in already_tested_seeds:
                continue
            already_tested_seeds.add(seed)
            self.parser.gamestate.seed = seed
            self.parser.gamestate.reset()
            events = self.parser.parse(input_text)
            damage_values.clear()
            for index in indexes:
                event: CharacterAction = events[index]
                damage_values.append(event.damage)
            if damage_values == input_dvs:
                self.input_widget.set_input(
                    f'# Seed number: {seed}\n{self.input_widget.get_input()}')
                self.warning_popup.print_output(f'Seed: {seed}')
                self.callback()
                break
        else:
            self.warning_popup.print_output('Seed not found!')
