import json 
from pprint import pprint

from bugbunnies.logging import getLogger

import paho.mqtt.client as mqtt

if __name__ == "__main__":
    client = mqtt.Client()

    def on_message(client, userdata, msg):
        logger.info(msg.topic + msg.payload.decode())
        pprint(json.loads(msg.payload.decode()))

    logger = getLogger(__name__)
    client.connect("localhost")
    client.subscribe("IRC", 0)
    client.on_message = on_message
    client.loop_forever()

    
