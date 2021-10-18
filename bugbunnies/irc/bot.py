"""An irc bot with a hammer"""
import copy
import importlib
import json
import signal
import threading
import traceback
import uuid

import yaml
import irc.bot  # type: ignore
import irc.client
from jaraco.stream import buffer
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

from bugbunnies.irc import reactions, commands
from bugbunnies.config import load_config

PROTOCOL = "irc"

class Bot(irc.bot.SingleServerIRCBot):
    def __init__(self, config: str, logger):
        irc.client.ServerConnection.buffer_class = buffer.LenientDecodingLineBuffer

        self.logger = logger
        self.config_path = config
        self.id = str(uuid.uuid4())

        load_config(self, PROTOCOL)


        self.server = irc.bot.ServerSpec(
            self.config.get("server", dict()).get("address", "localhost"),
            self.config.get("server", dict()).get("port", 6667)
        )

        strategy = irc.bot.ExponentialBackoff(
            min_interval=self.config.get("min_reconnect_interval", 5),
            max_interval=self.config.get("max_reconnect_interval", 1800),
        )

        super().__init__(
            [self.server],
            self.config.get("nick", "Roran"),
            self.config.get("realname", "Roran"),
            recon=strategy,
                )

        # mqtt client
        self.mqtt_client = mqtt.Client()
        
        self.mqtt_client.owner = self

        def on_message(client, userdata, msg):
            payload = json.loads(msg.payload.decode())
            if payload.get("bot_target", "") == client.owner.id:
                client.owner.logger.debug(f"{msg.payload.decode()}")
                client.owner.__handle_action(payload)

        self.mqtt_client.on_message = on_message


        # Add mqtt handler
        self.reactor.add_global_handler("all_events", self._publish, -10)


        self.logger.info("Init done")

    def __handle_action(self, payload):
        for message in payload.get("messages", []):
            self.connection.privmsg(message["target"], message["content"])
        for join in payload.get("join", []):
            self.connection.join(join)

    def start(self):
        self.mqtt_client.connect(
            self.config.get("mqtt", dict()).get("address", "localhost"),
            self.config.get("mqtt", dict()).get("port", 1883)
        )
        self.mqtt_client.subscribe(PROTOCOL, 0)
        th = threading.Thread(target=self.mqtt_client.loop_forever)
        th.start()
        super().start()
        th.join()

    def _publish(self, connection, event):
        event_dict = {
            "bot": self.id,
            "type": event.type,
            "source": event.source,
            "target": event.target,
            "arguments": event.arguments,
            "tags": event.tags
        }
        self.logger.debug(json.dumps(event_dict))
        publish.single(PROTOCOL, json.dumps(event_dict), hostname="localhost")

    def _get_command(self, message: str):
        if message.startswith(self.config.get("prefix", "!")) and len(message) > 1:
            message = message.split()
            command = message[0][1:]
            args = message[1:] if len(message) > 1 else []
            return (command, args)
        return False

    def on_welcome(self, c, e):
        if self.config.get("password"):
            c.privmsg("NickServ", text='RECOVER {} {}'.format(
                self.config.get("nick"),
                self.config.get("password")))
            c.nick(self.config.get("nick"))
            c.privmsg("NickServ", text='IDENTIFY {}'.format(
                self.config.get("password")))
        for chan in self.config.get("channels", []):
            c.join(chan)


    def on_invite(self, c, e):
        if e.source.nick not in self.config.get("blacklist"):
            c.join(e.arguments[0])

    def on_disconnect(self, c: irc.client.ServerConnection, e: irc.client.Event):
        self.logger.error("Lost connection")
        self.logger.debug(str(e))