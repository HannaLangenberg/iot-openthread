import logging
import time
import paho.mqtt.client as mqtt  # type: ignore
from paho.mqtt.enums import CallbackAPIVersion  # type: ignore
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logging.getLogger("coap_server").setLevel(logging.DEBUG)


class MqttClient:
    def __init__(self):
        self.client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    
    def connect_mqtt(self, mqtt_hostname, port, username, password, keepalive = 60, ):
        try:
            self.client.username_pw_set(username, password)
            self.client.connect(mqtt_hostname, port, keepalive)
            self.client.on_connect = on_connect
            # self.client.on_disconnect = on_disconnect
            self.client.loop_start()
        except ConnectionRefusedError as e:
            logging.error(f'Connection to MQTT failed: "{e}"')
        except Exception as e:
            logging.error(f'Exception while connecting to MQTT: "{e}"')
        
    def publish_mqtt_message(self, topic, payload):
        try:
            res = self.client.publish(
                topic=topic, 
                payload=payload
            )
            status = res[0]
            if status == 0:
                logging.info("Message published to topic " + topic)
                logging.debug("Message "+ str(payload) + " is published to topic " + topic)
            else:
                logging.error("Failed to send message to topic " + topic)
                if not self.client.is_connected():
                    logging.error("Client was not connected")
            
        except Exception as e:
            logging.error(f'Failed to publish topic {topic}: "{e}"')
    
    def disconnect_mqtt(self):
        try:
            self.client.disconnect()
            self.client.loop_stop()
        except Exception as e:
            logging.error(f'Failed to disconnect MQTT Client')


def on_connect(client, userdata, flags, return_code, properties):
    if return_code == 0:
        logging.info("Connected to MQTT Broker")
    else:
        logging.warning(f"Connection to MQTT failed with code {return_code}")


def on_disconnect(client, userdata, reason_code, properties):
    logging.warning(f"Lost connection to MQTT Server: {reason_code}")