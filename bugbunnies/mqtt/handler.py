import importlib
import json 
import traceback

from bugbunnies.logging import getLogger
from bugbunnies.config import load_config

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

from ping3 import ping

PROTOCOL = "mqtt"

class Handler(mqtt.Client):
    def __init__(self, config, logger):
        super().__init__()

        self.logger = logger

        self.config_path = config
        load_config(self, PROTOCOL)

        self.connect(
            self.config.get("server", dict()).get("address", "localhost"),
            self.config.get("server", dict()).get("port", 1883)
        )
        self.modules = []
        self.__load_modules()

        for topic in self.config.get("topics", []):
            self.subscribe(topic, 0)

# Messages handling

    def on_message(self, client, userdata, msg):
        self.logger.debug(f"{msg.topic} {msg.payload.decode()}")
        payload = json.loads(msg.payload.decode())
        if msg.topic == "irc" and payload.get("type") in ["pubmsg", "privmsg"]:
            self.__handle_message(msg.topic, payload)

    def __handle_message(self, topic, message):
        if action := self.__get_command(" ".join(message["arguments"])):
            self.logger.info(f"Found command {action}")
            actions = self.__apply_command(message, *action)
            self.__execute_command(topic, message, actions)
            for module in self.modules:
                actions = module.apply_command(self, message, *action)
                self.__execute_command(topic, message, actions)

# Commands handling

    def __get_command(self, message):
        if message.startswith(self.config.get("prefix", "!")) and len(message) > 1:
            message = message.split()
            command = message[0][1:]
            args = message[1:] if len(message) > 1 else []
            return (command, args)
        return False

    def __execute_command(self, topic, message, actions):
        if actions is not None:
            self.logger.warning(actions)
            actions["bot_target"] = message.get("bot")
            publish.single(topic, json.dumps(actions), hostname="localhost")
            

    def get_target(self, message):
        return message["source"] if message["type"] == "privmsg" else message["target"]

# Internal commands
    def __apply_command(self, message, command, arguments):
        # !reload
        if command == "reload":
            if self.__reload():
                return {"messages": [{"target": self.get_target(message), "content": "Reload done"}]}
            else: 
                return {"messages": [{"target": self.get_target(message), "content": "Reload failed"}]}

# Configuration

    def __load_modules(self):
        self.logger.info("Loading modules")
        self.modules = []
        for module_name in self.config.get("modules", []):
            real_name = f"bugbunnies.modules.{module_name}"
            self.logger.debug(f"Loading module {real_name}")
            try:
                module = importlib.import_module(real_name)
                module = importlib.reload(module)
                self.modules.append(module)
            except Exception:
                self.logger.error(f"Failed loading module {real_name}")

    def __reload(self):
        self.logger.info(f"Reloading bot")
        try:
            # rechargement du fichier de configuration
            # old_config = copy.deepcopy(self.config)
            load_config(self, PROTOCOL)
            # TODO: gérer les cas de changement de nick, realname et serveurs
            self.logger.debug("Reloading modules")
            self.__load_modules()
            self.logger.info(f"Reloading done")
            return True
        except Exception:
            self.logger.error(f"Reloading failed")
            trace = traceback.format_exc()
            self.logger.error(trace)
            return False

# Signals

    def __handle_signals(self, number, frame):
        self.logger.info(f"Received signal {number}")
        if number == signal.SIGHUP:
            self._reload()

# Start

    def start(self):
        self.loop_forever()       
