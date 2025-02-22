"""Configuration settings for the CoAP-MQTT bridge server."""

import os

# MQTT Configuration
MQTT_CONFIG = {
    "broker_addr": os.environ.get("MQTT_SERVER", "mosquitto"),
    "broker_port": int(os.environ.get("MQTT_PORT", 1883)),
    "username": os.environ.get("MQTT_USER", "admin"),
    "password": os.environ.get("MQTT_PASSWORD", "123456789"),
    "keepalive": 60
}

# CoAP Configuration
COAP_CONFIG = {
    "bind_addr": os.environ.get("COAP_BIND_NAME", "localhost"),
    "bind_port": int(os.environ.get("COAP_PORT", 5683))
}

# Topic Configuration
DEFAULT_TOPIC = "sensor/default"

# Location Mapping
LOCATION_MAPPING = {
    "3a:4f:ec:85:c0:65:36:19": "raum_1_08",
    "8e:d0:82:0b:a8:e5:c8:93": "roboterlabor",
    "52:9d:cd:3b:8a:73:dd:58": "besprechungsraum",
    "9a:d6:18:d1:e5:e5:7d:4b": "uic",
    "be:73:09:12:a3:31:2e:52": "erste_etage_flur"
}