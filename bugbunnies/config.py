import argparse

import yaml

class Parser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__()
        self.add_argument(
            "-v", "--verbose", action="count", default=0, help="verbosity level"
        )
        self.add_argument(
            "-c",
            "--config",
            type=str,
            default=None,
            help="use specified configuration file",
        )
        self.add_argument(
            "-l",
            "--log-path",
            type=str,
            default=None,
            help="Logs path"
        )

def load_config(inst, section):
    with open(inst.config_path) as configFile:
        inst.config = yaml.load(configFile, Loader=yaml.FullLoader).get(section, {})
    inst.logger.info(f"Loaded config from {inst.config_path} with section {section}")
    inst.logger.debug(str(inst.config))