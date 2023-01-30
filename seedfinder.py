from ffx_rng_tracker.configs import Configs
from ffx_rng_tracker.logger import setup_main_logger
from ffx_rng_tracker.ui_tkinter.main import main
from ffx_rng_tracker.ui_tkinter.seedfinder import TkSeedFinder

if __name__ == '__main__':
    setup_main_logger()
    Configs.init_configs()
    Configs.seed = 0
    main(TkSeedFinder, 'FFX Seedfinder', '800x600')
