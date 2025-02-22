"""Main CoAP-MQTT bridge server implementation."""

import asyncio
import logging
import aiocoap
import aiocoap.resource as resource
from .config import COAP_CONFIG
from .mqtt_handler import MQTTHandler
from .resources import MQTTBridgeResource

class CoAPServer:
    def __init__(self):
        self.logger = logging.getLogger("coap_server")
        self.mqtt_handler = MQTTHandler()
        
    def _setup_resources(self) -> resource.Site:
        """Setup CoAP resource tree."""
        root = resource.Site()
        
        # Add core resource for service discovery
        root.add_resource(
            [".well-known", "core"],
            resource.WKCResource(root.get_resources_as_linkheader)
        )
        
        # Add MQTT bridge resource
        root.add_resource(['sensor'], MQTTBridgeResource(self.mqtt_handler))
        
        return root

    async def start(self):
        """Start the CoAP server."""
        try:
            # Start MQTT handler
            if not await self.mqtt_handler.connect():  # Make connect async
                self.logger.error("Failed to connect to MQTT broker")
                return
            await self.mqtt_handler.start()  # Make start async

            # Setup and start CoAP server
            root = self._setup_resources()
            await aiocoap.Context.create_server_context(
                root,
                bind=(COAP_CONFIG["bind_addr"], COAP_CONFIG["bind_port"])
            )
            
            self.logger.info(
                f"CoAP server started on {COAP_CONFIG['bind_addr']}:{COAP_CONFIG['bind_port']}"
            )
            
            # Keep the server running
            await asyncio.get_running_loop().create_future()
            
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            await self.mqtt_handler.stop()  # Make stop async

def main():
    """Entry point for the CoAP-MQTT bridge server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s %(name)s %(levelname)s]: %(message)s'
    )
    
    # Start server
    server = CoAPServer()
    asyncio.run(server.start())

if __name__ == "__main__":
    main()