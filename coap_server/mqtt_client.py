import logging
import random
import time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)  # "CoAP_mqtt_client")
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)


def connect_mqtt(
        broker: str,
        username: str, 
        password: str,
        port: int = 1833,
        keepalive: int = 60, 
    ):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker")
        else:
            logging.warning(f"Connection to MQTT failed with code {rc}")

    def on_disconnect(client, userdata, reason_code, properties):
        logging.warning(f"Lost connection to MQTT Server: {reason_code}")

    try:
        client.username_pw_set(username, password=password)
        client.connect(broker, port, keepalive)
        # client.on_connect = on_connect # TODO will nich
        # client.on_disconnect = on_disconnect
        client.loop_start()
    except ConnectionRefusedError as e:
        logging.error(f'Connection to MQTT failed: "{e}"')
    except Exception as e:
        logging.error(f'Exception in MQTT lib: "{e}"')

def publish_mqtt_message():
    msg_count = 0
    topic = 'test_topic/test/'
    humidity = 21
    temperature = 29
    battery_voltage_mv = 26
    
    # Publish to MQTT Broker
    try:
        while msg_count < 10:
            time.sleep(10)    
            msg_count += 1
            humidity += random.randint(1, 5)
            temperature += random.randint(1, 5)
            battery_voltage_mv += random.randint(1, 5)
            payload = f'{{"humidity":{humidity}, "temperature":{temperature}, "battery_voltage_mv":{battery_voltage_mv}}}'
            res = client.publish(
                topic=topic, 
                payload=payload
            )
            status = res[0]
            if status == 0:
                logging.info("Message "+ str(msg_count) + " is published to topic " + topic)
            else:
                logging.error("Failed to send message to topic " + topic)
                if not client.is_connected():
                    logging.error("Client not connected, exiting...")
                    break
    except Exception as e:
        logging.error(f'Failed to publish topic {topic}: "{e}"')
    finally:
        client.disconnect()
        client.loop_stop()

if __name__ == "__main__":
    broker_hostname = "mosquitto"
    port = 1883
    user = "admin"
    password = "123456789"
    connect_mqtt(broker_hostname, user, password, port=port)
    

    publish_mqtt_message()
