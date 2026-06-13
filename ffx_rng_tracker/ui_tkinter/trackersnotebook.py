import tkinter as tk
from logging import getLogger
from tkinter import ttk

from ..configs import Configs, UIWidgetConfigs
from ..data.constants import UIWidget
from ..events.parser import EventParser
from ..gamestate import GameState
from ..tracker import FFXRNGTracker
from .actions_tracker import TkActionsTracker
from .configslog import TkConfigsLogViewer
from .drops_tracker import TkDropsTracker
from .encounters_planner import TkEncountersPlanner
from .encounters_table import TkEncountersTable
from .encounters_tracker import TkEncountersTracker
from .monster_data_viewer import TkMonsterDataViewer
from .seed_info import TkSeedInfo
from .seedfinder import TkSeedFinder
from .steps_tracker import TkStepsTracker
from .tktracker import TkTracker
from .yojimbo_tracker import TkYojimboTracker


class TkTrackersNotebook(ttk.Notebook):
    def __init__(self, parent, *args, **kwargs) -> None:
        super().__init__(parent, *args, **kwargs)

        seed_info_configs = Configs.ui_widgets[UIWidget.SEED_INFO]
        self.seed_info = TkSeedInfo(self, seed_info_configs)
        self.add(self.seed_info, text=UIWidget.SEED_INFO)

        m_d_configs = Configs.ui_widgets[UIWidget.MONSTER_DATA]
        if m_d_configs.shown:
            if m_d_configs.windowed:
                window = self.make_new_toplevel(UIWidget.MONSTER_DATA, m_d_configs)
                self.monster_data = TkMonsterDataViewer(window, m_d_configs)
                self.monster_data.pack(expand=True, fill='both')
            else:
                self.monster_data = TkMonsterDataViewer(self, m_d_configs)
                self.add(self.monster_data, text=UIWidget.MONSTER_DATA)
        else:
            self.monster_data = None

        c_l_configs = Configs.ui_widgets[UIWidget.CONFIGS]
        if c_l_configs.shown:
            if c_l_configs.windowed:
                window = self.make_new_toplevel(UIWidget.CONFIGS, c_l_configs)
                self.configs_log = TkConfigsLogViewer(window, c_l_configs)
                self.configs_log.pack(expand=True, fill='both')
            else:
                self.configs_log = TkConfigsLogViewer(self, c_l_configs)
                self.add(self.configs_log, text=UIWidget.CONFIGS)
        else:
            self.configs_log = None

        self.trackers: list[TkTracker] = []
        if Configs.seed is None:
            self.seed_info.register_callback(self.first_seed_callback_func)
        else:
            self.first_seed_callback_func(Configs.seed)
            self.seed_info.print_output(Configs.seed)

    def first_seed_callback_func(self,
                                 seed: int,
                                 _: bool | None = None,
                                 ) -> None:
        root = self.winfo_toplevel()
        title = root.title()
        root.title(f'{title} | Seed: {seed}')
        getLogger(__name__).info(f'Opened with seed {seed}.')
        for tracker_type in TRACKERS:
            self.add_tracker(tracker_type, seed)
        if (self.monster_data is not None
                and self.monster_data.winfo_parent() == str(self)):
            self.insert('end', self.monster_data)
        if (self.configs_log is not None
                and self.configs_log.winfo_parent() == str(self)):
            self.insert('end', self.configs_log)
        self.seed_info.register_callback(self.reload_seed_callback_func)

    def reload_seed_callback_func(self, seed: int, reload_notes: bool) -> None:
        root = self.winfo_toplevel()
        title = root.title().split(' | Seed: ')[0]
        root.title(f'{title} | Seed: {seed}')
        getLogger(__name__).info(f'Changed seed to {seed}.')
        for tracker in self.trackers:
            tracker.tracker.change_seed(seed, reload_notes)

    def make_new_toplevel(self, title: str, configs: UIWidgetConfigs) -> tk.Toplevel:
        window = tk.Toplevel()
        window.title(title)
        window.geometry(str(configs.geometry))
        window.protocol('WM_DELETE_WINDOW', lambda: None)
        return window

    def add_tracker(self, tracker_type: type[TkTracker], seed: int) -> None:
        name = tracker_type.tracker_type.name
        configs = Configs.ui_widgets[name]
        if not configs.shown:
            return
        parser = EventParser(GameState(FFXRNGTracker(seed)))
        if configs.windowed:
            window = self.make_new_toplevel(name, configs)
            tracker = tracker_type(window, parser, configs)
            tracker.pack(expand=True, fill='both')
        else:
            tracker = tracker_type(self, parser, configs)
            self.add(tracker, text=name)
        self.trackers.append(tracker)


TRACKERS: tuple[type[TkTracker], ...] = (
    TkDropsTracker,
    TkEncountersTracker,
    TkStepsTracker,
    TkEncountersPlanner,
    TkEncountersTable,
    TkActionsTracker,
    TkYojimboTracker,
    TkSeedFinder,
)
