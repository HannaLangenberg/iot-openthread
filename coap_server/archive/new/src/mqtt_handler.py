"""MQTT client handler implementation."""

import logging
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from .config import MQTT_CONFIG

class MQTTHandler:
    def __init__(self):
        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.logger = logging.getLogger("mqtt_handler")

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            self.logger.info("MQTT Connected successfully!")
        else:
            self.logger.error(f"MQTT Connection failed with code {rc}")

    def _on_message(self, client, userdata, msg, properties):
        self.logger.info(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
        client.publish("iot/echo", msg.payload.decode())

    async def connect(self) -> bool:
        """Establish connection to MQTT broker."""
        try:
            self.client.username_pw_set(
                username=MQTT_CONFIG["username"],
                password=MQTT_CONFIG["password"]
            )
            self.client.connect(
                MQTT_CONFIG["broker_addr"],
                port=MQTT_CONFIG["broker_port"],
                keepalive=MQTT_CONFIG["keepalive"]
            )
            return True
        except Exception as e:
            self.logger.error(f"MQTT connection error: {e}")
            return False

    async def publish(self, topic: str, payload: str) -> bool:
        """Publish message to MQTT broker."""
        try:
            result = self.client.publish(topic=topic, payload=payload)
            if result[0] == 0:
                self.logger.info(f"Published to topic: {topic}")
                return True
            self.logger.error(f"Failed to publish to topic: {topic}")
            return False
        except Exception as e:
            self.logger.error(f"Error publishing to MQTT: {e}")
            return False

    async def start(self):
        """Start MQTT client loop."""
        self.client.loop_start()

    async def stop(self):
        """Stop MQTT client loop."""
        self.client.loop_stop()