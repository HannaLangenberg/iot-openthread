import logging
import random
import time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from datetime import datetime
import json

client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)  # "CoAP_mqtt_client")
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap_server").setLevel(logging.DEBUG)

examples = {
    "52:9d:cd:3b:8a:73:dd:58":
    {
        "mac_addr":      "52:9d:cd:3b:8a:73:dd:58",
        "RLOC16":        "0x6000",
        "timestamp_ms":  78008155,
        "tx_pwr":        20,
        "MAC_RxErrFcs":  0,
        "MAC_TxErrAbort":0,
        "IP_RxFailures": 0,
        "IP_TxFailures": 0,
        "temperature":   19.59375,
        "humidity":      85.1875,
        "neighbor_rssi": [
            {
                "MAC": "8e:d0:82:0b:a8:e5:c8:93",
                "RSSI_AVG": -22
            },
            {
                "MAC": "3a:4f:ec:85:c0:65:36:19",
                "RSSI_AVG": -45
            },
            {
                "MAC": "8a:00:f6:c3:24:52:4d:25",
                "RSSI_AVG": -78
            },
        ]
    },
    "8e:d0:82:0b:a8:e5:c8:93":
    {
        "mac_addr":      "8e:d0:82:0b:a8:e5:c8:93",
        "RLOC16":        "0x6000",
        "timestamp_ms":  78008155,
        "tx_pwr":        21,
        "MAC_RxErrFcs":  0,
        "MAC_TxErrAbort":0,
        "IP_RxFailures": 0,
        "IP_TxFailures": 0,
        "temperature":   21.7812,
        "humidity":      81.5677,
        "neighbor_rssi": [
            {
                "MAC": "52:9d:cd:3b:8a:73:dd:58",
                "RSSI_AVG": -12
            },
            {
                "MAC": "3a:4f:ec:85:c0:65:36:19",
                "RSSI_AVG": -23
            },
            {
                "MAC": "8a:00:f6:c3:24:52:4d:25",
                "RSSI_AVG": -34
            },
        ]
    },
    "3a:4f:ec:85:c0:65:36:19":
    {
        "mac_addr":      "3a:4f:ec:85:c0:65:36:19",
        "RLOC16":        "0x6000",
        "timestamp_ms":  78008155,
        "tx_pwr":        22,
        "MAC_RxErrFcs":  0,
        "MAC_TxErrAbort":0,
        "IP_RxFailures": 0,
        "IP_TxFailures": 0,
        "temperature":   23.4567,
        "humidity":      28.3453,
        "neighbor_rssi": [
            {
                "MAC": "52:9d:cd:3b:8a:73:dd:58",
                "RSSI_AVG": -78
            },
            {
                "MAC": "8e:d0:82:0b:a8:e5:c8:93",
                "RSSI_AVG": -23
            },
            {
                "MAC": "8a:00:f6:c3:24:52:4d:25",
                "RSSI_AVG": -48
            },
        ]
    },
    "8a:00:f6:c3:24:52:4d:25":
    {
        "mac_addr":      "8a:00:f6:c3:24:52:4d:25",
        "RLOC16":        "0x6000",
        "timestamp_ms":  78008155,
        "tx_pwr":        23,
        "MAC_RxErrFcs":  0,
        "MAC_TxErrAbort":0,
        "IP_RxFailures": 0,
        "IP_TxFailures": 0,
        "temperature":   87.3242,
        "humidity":      43.4657,
        "neighbor_rssi": [
            {
                "MAC": "52:9d:cd:3b:8a:73:dd:58",
                "RSSI_AVG": -26
            },
            {
                "MAC": "8e:d0:82:0b:a8:e5:c8:93",
                "RSSI_AVG": -38
            },
            {
                "MAC": "3a:4f:ec:85:c0:65:36:19",
                "RSSI_AVG": -26
            },
        ]
    },
}

def connect_mqtt(
        broker: str,
        username: str, 
        password: str,
        port: int = 1883,
        keepalive: int = 60, 
    ):
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            logging.info("Connected to MQTT Broker")
        else:
            logging.warning(f"Connection to MQTT failed with code {rc}")

    try:
        client.username_pw_set(username, password=password)
        client.connect(broker, port, keepalive)
        client.on_connect = on_connect
        client.loop_start()
    except ConnectionRefusedError as e:
        logging.error(f'Connection to MQTT failed: "{e}"')
    except Exception as e:
        logging.error(f'Exception in MQTT lib: "{e}"')

def publish_mqtt_message():
    msg_count = 0
    base_topic = 'sensor/'
    
    # Publish to MQTT Broker
    try:
        while msg_count < 10:
            msg_count += 1
            for node, values in examples.items():
                topic = base_topic + node
                h = values["humidity"] + random.randint(-5, 5)
                t = values["temperature"] + random.randint(-5, 5)
                for neighbor in values["neighbor_rssi"]:
                    neighbor["RSSI_AVG"] += random.randint(-5, 5)
                timestamp = datetime.now().timestamp()
                
                values["humidity"] = h
                values["temperature"] = t
                values["timestamp_ms"] = timestamp
                
                json_string = json.dumps(values)
                res = client.publish(
                    topic=topic, 
                    payload=json_string
                )
                status = res[0]
                if status == 0:
                    logging.info("Message "+ str(msg_count) + " is published to topic " + topic)
                else:
                    logging.error("Failed to send message to topic " + topic)
                    if not client.is_connected():
                        logging.error("Client not connected, exiting...")
                        break
            time.sleep(10)
            
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
