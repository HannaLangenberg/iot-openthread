"""CoAP resource implementations."""

import json
import logging
from urllib.parse import urlparse
import aiocoap.resource as resource
from aiocoap import Message, Code
from aiocoap.numbers.contentformat import ContentFormat
from .config import DEFAULT_TOPIC, LOCATION_MAPPING

class MQTTBridgeResource(resource.Resource):
    def __init__(self, mqtt_handler):
        super().__init__()
        self.mqtt_handler = mqtt_handler
        self.logger = logging.getLogger("mqtt_bridge")

    def _process_payload(self, payload_data: dict) -> tuple[str, str]:
        """Process and enhance payload data with location information."""
        mac_address = list(payload_data.values())[0].lower().replace(" ", "")
        
        if mac_address in LOCATION_MAPPING:
            payload_data["location"] = LOCATION_MAPPING[mac_address]
            
            for neighbor in payload_data.get("neighbor_rssi", []):
                neighbor["neighbor_location"] = LOCATION_MAPPING.get(neighbor["MAC"])
                
            topic = f"{DEFAULT_TOPIC}/{payload_data['location']}"
        else:
            topic = f"{DEFAULT_TOPIC}/{mac_address}"
            
        return topic, json.dumps(payload_data)

    async def render(self, request: Message):
        try:
            request_uri = urlparse(request.get_request_uri())
            topic_base = str(request_uri.path).removeprefix('/')
            if not topic_base or topic_base in ['/', '()', '#', '$']:
                topic_base = DEFAULT_TOPIC

            payload = request.payload.decode('utf-8')
            payload_data = json.loads(payload)
            
            topic, processed_payload = self._process_payload(payload_data)
            
            if self.mqtt_handler.publish(topic, processed_payload):
                return Message(
                    code=Code.CONTENT,
                    payload=f"Published {len(request.payload)} bytes".encode()
                )
            else:
                return Message(
                    code=Code.INTERNAL_SERVER_ERROR,
                    payload=b"Failed to publish message"
                )
                
        except Exception as e:
            self.logger.error(f"Error processing request: {e}")
            return Message(
                code=Code.INTERNAL_SERVER_ERROR,
                payload=str(e).encode()
            )