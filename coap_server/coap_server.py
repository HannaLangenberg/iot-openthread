"""
This script sets up a CoAP server with various resources using the aiocoap library 
and bridges it with MQTT.

Authors:
    - Jannik Schmöle
    - Mohamed Chamharouch Aukili

Imports:
    Standard library:
    - asyncio: Used for asynchronous programming and event loop management
    - json: Used for parsing and creating JSON data
    - logging: Used for logging information and debugging messages
    - os: Used for environment variables
    - datetime: Used for generating current time in TimeResource
    - urllib.parse: Used for parsing URIs

    CoAP related:
    - aiocoap: Provides core functionalities for CoAP protocol
    - aiocoap.resource: Provides base classes for defining CoAP resources
    - aiocoap.Message, Code: Used for creating CoAP messages and response codes
    - aiocoap.numbers.contentformat: Used for specifying content formats

    MQTT related:
    - paho.mqtt.client: MQTT client implementation
    - paho.mqtt.enums: MQTT callback API version constants

Classes:
    MQTT_Bridge(resource.Resource):
        Bridges CoAP requests to MQTT publications

    AllResourcesHandler(resource.Resource):
        Generic handler for all resources

    Welcome(resource.Resource):
        Welcome page with multiple representations

    BlockResource(resource.Resource):
        Demonstrates blockwise transfers

    SeparateLargeResource(resource.Resource):
        Demonstrates separate responses

    TimeResource(resource.ObservableResource):
        Observable time resource

    WhoAmI(resource.Resource):
        Reports client network information
"""
# Standard library imports
import asyncio
import json
import logging
import os
from datetime import datetime
from urllib.parse import urlparse

# Third-party imports - CoAP related
import aiocoap  # type: ignore
import aiocoap.resource as resource  # type: ignore
from aiocoap import Message, Code  # type: ignore
from aiocoap.numbers.contentformat import ContentFormat  # type: ignore

# Third-party imports - MQTT related
import paho.mqtt.client as mqtt  # type: ignore
from paho.mqtt.enums import CallbackAPIVersion  # type: ignore

locations = {
    "3a:4f:ec:85:c0:65:36:19" : "raum_1_08",
    "8e:d0:82:0b:a8:e5:c8:93" : "roboterlabor",
    "52:9d:cd:3b:8a:73:dd:58" : "besprechungsraum",
    "9a:d6:18:d1:e5:e5:7d:4b" : "uic",
    "be:73:09:12:a3:31:2e:52" : "erste_etage_flur"
}

# Constants
DEFAULT_TOPIC = "sensor/default"
LOG_FORMAT = '[%(asctime)s %(name)s %(levelname)s]: %(message)s'
LOGGER_NAME = "coap2mqtt"

# Configure logging with proper formatting and level
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT
)
log = logging.getLogger(LOGGER_NAME)

# Initialize MQTT client with modern API version
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)

class MQTT_Bridge(resource.Resource):
    """
    MQTT Bridge Resource Handler for CoAP-to-MQTT Message Forwarding
    This class handles CoAP requests and forwards their payloads to an MQTT broker. It processes
    incoming CoAP messages, extracts topics from the request URI, handles JSON payloads with 
    device information including MAC addresses and neighbor RSSI data, and maps locations.
    Attributes:
        DEFAULT_TOPIC (str): Default MQTT topic used when path extraction fails
        locations (dict): Mapping of MAC addresses to physical locations
        client (mqtt.Client): MQTT client instance for publishing
    Methods:
        render(request: Message) -> Message:
            Handles incoming CoAP requests and publishes their payload to MQTT broker
    Example:
        >>> bridge = MQTT_Bridge()
        >>> # When receiving CoAP request with JSON payload:
        >>> # {
        >>> #    "mac_addr": "00:11:22:33:44:55",
        >>> #    ...
        >>> #    "neighbor_rssi": [{..., "MAC": "aa:bb:cc:dd:ee:ff", "RSSI_AVG": -70}]
        >>> # }
        >>> # Publishes to MQTT with location mapping and returns confirmation
    Note:
        - Expects JSON formatted payloads
        - Handles MAC address normalization (lowercase, no spaces)
        - Maps device locations based on MAC addresses
        - Adds location information to neighbor devices
        - Constructs MQTT topic as "{topic}/{location}" or "{topic}/{mac_address}"
        - Provides detailed logging of operations and errors
    Raises:
        json.JSONDecodeError: If payload is not valid JSON
        Exception: For general errors during message processing or MQTT publishing
    """
    async def render(self, request: Message):
        """Handle incoming CoAP requests and forward to MQTT broker.
        
        Args:
            request (Message): Incoming CoAP request
            
        Returns:
            Message: CoAP response message
        """
        topic = self._extract_topic(request)
        payload = request.payload.decode('utf-8')
        
        log.info(f"Processing CoAP request from {request.remote.hostinfo.split(':')[0]}")
        log.debug(f"Request details - URI: {request.get_request_uri()}, Code: {request.code}")
        log.debug(f"Received payload: {payload}")

        try:
            parsed_data = json.loads(payload)
            enriched_data = self._enrich_data_with_locations(parsed_data)
            topic = self._build_mqtt_topic(topic, enriched_data)
            
            self._publish_to_mqtt(topic, enriched_data)
            
            return Message(
                code=Code.CONTENT,
                payload=f"Successfully published {len(request.payload)} bytes".encode()
            )
            
        except json.JSONDecodeError:
            log.error("Failed to parse JSON payload")
            return Message(code=Code.BAD_REQUEST)
        except Exception as e:
            log.error(f"Error processing request: {str(e)}")
            return Message(code=Code.INTERNAL_SERVER_ERROR)

    def _extract_topic(self, request: Message) -> str:
        """Extract MQTT topic from CoAP request URI."""
        try:
            request_uri = urlparse(request.get_request_uri())
            topic = str(request_uri.path).removeprefix('/')
            return topic if topic and topic not in ['/', '()', '#', '$'] else DEFAULT_TOPIC
        except:
            log.error("Failed to extract topic from request URI")
            return DEFAULT_TOPIC

    def _enrich_data_with_locations(self, data: dict) -> dict:
        """Add location information to device and neighbor data."""
        mac_address = list(data.values())[0].lower().replace(" ", "")
        
        if mac_address in locations:
            data["location"] = locations[mac_address]
            
        for neighbor in data["neighbor_rssi"]:
            if neighbor["MAC"] in locations:
                neighbor["neighbor_location"] = locations[neighbor["MAC"]]
                
        return data

    def _build_mqtt_topic(self, base_topic: str, data: dict) -> str:
        """Construct full MQTT topic path."""
        mac_address = list(data.values())[0].lower().replace(" ", "")
        location_or_mac = data.get("location", mac_address)
        return f"{base_topic}/{location_or_mac}"

    def _publish_to_mqtt(self, topic: str, data: dict) -> None:
        """Publish enriched data to MQTT broker."""
        payload = json.dumps(data)
        result = client.publish(topic=topic, payload=payload)
        
        if result[0] == 0:
            log.info(f"Successfully published message to MQTT topic: {topic}")
            log.debug(f"Published payload: {payload}")
        else:
            log.error(f"Failed to publish to MQTT topic: {topic}")
            if not client.is_connected():
                log.error("MQTT client connection lost")

# Handler for all resources, responds with a generic message
class AllResourcesHandler(resource.Resource):
    async def render(self, request: Message):
        # Log the received request
        logging.info(f"Received request: {request.code} on {request.opt.uri_path}")
        logging.info(f"Payload: {request.payload.decode('utf-8')}")

        # Respond with a generic message
        return Message(
            code=Code.CONTENT,
            payload=b"Generic response for any resource"
        )

# Welcome resource with multiple representations
class Welcome(resource.Resource):
    representations = {
        ContentFormat.TEXT: b"Welcome to the demo server",
        ContentFormat.LINKFORMAT: b"</.well-known/core>,ct=40",
        ContentFormat(65000): (
            b'<html xmlns="http://www.w3.org/1999/xhtml">'
            b"<head><title>aiocoap demo</title></head>"
            b"<body><h1>Welcome to the aiocoap demo server!</h1>"
            b'<ul><li><a href="time">Current time</a></li>'
            b'<li><a href="whoami">Report my network address</a></li>'
            b"</ul></body></html>"
        ),
    }
    default_representation = ContentFormat.TEXT

    async def render_get(self, request):
        logging.info(f"Received GET request: {request}")
        # Determine the content format to respond with
        cf = (
            self.default_representation
            if request.opt.accept is None
            else request.opt.accept
        )

        try:
            return aiocoap.Message(payload=self.representations[cf], content_format=cf)
        except KeyError:
            raise aiocoap.error.UnsupportedContentFormat

# Resource that supports GET and PUT methods with blockwise transfer
class BlockResource(resource.Resource):
    def __init__(self):
        super().__init__()
        self.set_content(
            b"This is the resource's default content. It is padded "
            b"with numbers to be large enough to trigger blockwise "
            b"transfer.\n"
        )

    def set_content(self, content):
        # Set the initial content
        self.content = content
        
        # Calculate the number of times to repeat the padding string to reach the desired length
        padding = b"\x00"
        repeat_count = 1024 - len(self.content)
        
        # Append the padding string the calculated number of times
        self.content += padding * repeat_count
        
        # Ensure the content is exactly 1024 bytes long
        self.content = self.content[:1024]

    async def render_get(self, request):
        logging.info(f"Received GET request from {request.remote.hostinfo}")
        return aiocoap.Message(payload=self.content)

    async def render_put(self, request):
        logging.info(f"PUT payload: {request.payload}")
        self.set_content(request.payload)
        return aiocoap.Message(code=aiocoap.CHANGED, payload=self.content)

# Resource that simulates a long-running operation
class SeparateLargeResource(resource.Resource):
    def get_link_description(self):
        # Publish additional data in .well-known/core
        return dict(**super().get_link_description(), title="A large resource")

    async def render_get(self, request):
        await asyncio.sleep(3)  # Simulate long-running operation

        payload = (
            "Three rings for the elven kings under the sky, seven rings "
            "for dwarven lords in their halls of stone, nine rings for "
            "mortal men doomed to die, one ring for the dark lord on his "
            "dark throne.".encode("ascii")
        )

        return aiocoap.Message(payload=payload)

# Observable resource that provides the current time
class TimeResource(resource.ObservableResource):
    def __init__(self):
        super().__init__()
        self.handle = None  # Handle for the scheduled notification

    def notify(self):
        """Notify observers with the updated state."""
        self.updated_state()
        self.reschedule()

    def reschedule(self):
        self.handle = asyncio.get_event_loop().call_later(5, self.notify)

    def update_observation_count(self, count):
        if count and self.handle is None:
            logging.info("Starting the clock")
            self.reschedule()
        elif count == 0 and self.handle:
            logging.info("Stopping the clock")
            self.handle.cancel()
            self.handle = None

    async def render_get(self, request):
        # Log the received request
        logging.info(f"Received GET request from {request.remote.hostinfo}")

        payload = datetime.now().strftime("%Y-%m-%d %H:%M:%S").encode("ascii")
        return aiocoap.Message(payload=payload, content_format=ContentFormat.TEXT)

# Resource that reports the client's network address
class WhoAmI(resource.Resource):
    async def render_get(self, request):
        text = [
            f"Used protocol: {request.remote.scheme}.",
            f"Request came from {request.remote.hostinfo}.",
            f"The server address used {request.remote.hostinfo_local}."
        ]

        claims = list(request.remote.authenticated_claims)
        if claims:
            text.append(f"Authenticated claims of the client: {', '.join(repr(c) for c in claims)}.")
        else:
            text.append("No claims authenticated.")

        return aiocoap.Message(content_format=0, payload="\n".join(text).encode("utf8"))

# MQTT Callbacks
def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        log.info("Connected successfully!")
    else:
        log.error(f"Connection failed with code {rc}")

def on_message(client, userdata, msg, properties):
    log.info(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    client.publish("iot/echo", msg.payload.decode())

async def loop_coap() -> None:
    """Initialize and run the CoAP server with configured resources.
    
    Sets up the resource tree, configures well-known endpoints for CoRE protocol discovery,
    and starts the CoAP server on the specified address and port.
    
    The server provides the following endpoints:
    - /.well-known/core: Resource discovery (CoRE Link Format)
    - /: Welcome page with multiple representations
    - /time: Observable current time resource
    - /whoami: Client network information
    - /sensor: MQTT bridge for sensor data
    
    Environment Variables:
        COAP_BIND_NAME (str): Hostname to bind the server to (default: "localhost")
        COAP_PORT (int): Port number for the CoAP server (default: 5683)
    
    Note:
        Port 5683 is standard for unencrypted CoAP
        Port 5684 is standard for DTLS-secured CoAP
    """
    # Initialize resource tree
    root = resource.Site()

    # Configure CoRE resource discovery
    root.add_resource(
        [".well-known", "core"], 
        resource.WKCResource(root.get_resources_as_linkheader)
    )

    # Add application resources
    root.add_resource([], Welcome())
    root.add_resource(["time"], TimeResource())
    root.add_resource(["whoami"], WhoAmI())
    root.add_resource(['sensor'], MQTT_Bridge())

    # Configure server address from environment
    coap_addr = os.environ.get("COAP_BIND_NAME", "localhost")
    coap_port = int(os.environ.get("COAP_PORT", 5683))
    
    # Start server context
    await aiocoap.Context.create_server_context(root, bind=(coap_addr, coap_port))
    
    # Keep server running indefinitely
    await asyncio.get_running_loop().create_future()


async def main() -> None:
    """Initialize and run the MQTT client and CoAP server.
    
    Sets up MQTT client connection with credentials and starts both
    the MQTT client loop and CoAP server.
    
    Environment Variables:
        MQTT_SERVER (str): MQTT broker address (default: "mosquitto")
        MQTT_PORT (int): MQTT broker port (default: 1883)
        MQTT_USER (str): MQTT username (default: "admin")
        MQTT_PASSWORD (str): MQTT password (default: "123456789")
    
    Raises:
        ConnectionRefusedError: If MQTT broker connection fails
        Exception: For other MQTT-related errors
    """
    # Configure MQTT callbacks
    client.on_connect = on_connect
    client.on_message = on_message

    # Configure MQTT connection parameters
    broker_addr = os.environ.get("MQTT_SERVER", "mosquitto")
    broker_port = int(os.environ.get("MQTT_PORT", 1883))
    log.info(f'Connecting to "mqtt://{broker_addr}:{broker_port}" ...')

    try:
        # Setup MQTT authentication
        client.username_pw_set(
            username=os.environ.get("MQTT_USER", "admin"),
            password=os.environ.get("MQTT_PASSWORD", "123456789")
        )
        # Establish MQTT connection
        client.connect(
            broker_addr,
            port=broker_port,
            keepalive=60
        )
    except ConnectionRefusedError as e:
        log.error(f'MQTT connection failed: "{e}"')
        raise
    except Exception as e:
        log.error(f'MQTT client error: "{e}"')
        raise

    # Start services
    client.loop_start()
    await loop_coap()

if __name__ == "__main__":
    asyncio.run(main())
