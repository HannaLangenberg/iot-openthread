import logging
import os
import random
import time
import paho.mqtt.client as mqtt  # type: ignore
from paho.mqtt.enums import CallbackAPIVersion  # type: ignore
from datetime import datetime
import json
from coap_server.src.archive.mqtt_client import MqttClient

client = MqttClient()
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap_server").setLevel(logging.DEBUG)


example_payload = {
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
}

dummy_data = {
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

def publish_messages_periodically():
    msg_count = 0
    base_topic = 'sensor/'
    
    # Publish to MQTT Broker
    try:
        while msg_count < 10:
            msg_count += 1
            for node, values in dummy_data.items():
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
                client.publish_mqtt_message(topic=topic, payload=json_string)
                
            time.sleep(10)
            
    finally:
        client.disconnect_mqtt()

if __name__ == "__main__":
    mqtt_hostname = "mosquitto"
    port = int(os.getenv('MOSQUITTO_PORT', 1883))
    user = os.getenv('MOSQUITTO_USERNAME', "admin")
    password = os.getenv('MOSQUITTO_PASSWORD', "123456789")
    client.connect_mqtt(mqtt_hostname, port, user, password)

    publish_messages_periodically()
