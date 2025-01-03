"""
This script sets up a CoAP server with various resources using the aiocoap library.

Imports:
    from datetime import datetime: Used for generating current time in TimeResource.
    import logging: Used for logging information and debugging messages.
    import asyncio: Used for asynchronous programming and event loop management.
    import aiocoap.resource as resource: Provides base classes for defining CoAP resources.
    from aiocoap.numbers.contentformat import ContentFormat: Used for specifying content formats in responses.
    import aiocoap: Provides core functionalities for CoAP protocol.
    from aiocoap import Message, Code: Used for creating CoAP messages and specifying response codes.

Classes:
    AllResourcesHandler(resource.Resource):
        Handles all resources and responds with a generic message.

    Welcome(resource.Resource):
        Provides a welcome message with multiple representations.

    BlockResource(resource.Resource):
        Supports GET and PUT methods with blockwise transfer.

    SeparateLargeResource(resource.Resource):
        Simulates a long-running operation and provides a large resource.

    TimeResource(resource.ObservableResource):
        Provides the current time and supports observation.

    WhoAmI(resource.Resource):
        Reports the client's network address.

Functions:
    main():
        Sets up the CoAP server, creates resource trees, and runs the event loop.

Entry Point:
    If the script is run directly, the main function is executed.
"""
import asyncio
import logging
from datetime import datetime

import aiocoap  # type: ignore
import aiocoap.resource as resource  # type: ignore
from aiocoap import Message, Code  # type: ignore
from aiocoap.numbers.contentformat import ContentFormat  # type: ignore

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
        cf = self.default_representation if request.opt.accept is None else request.opt.accept

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

# Logging setup
logging.basicConfig(level=logging.INFO)
logging.getLogger("coap-server").setLevel(logging.DEBUG)

async def main():
    # Print a message to the console
    print("Hello world")
    # Log an informational message
    logging.info("HELLO WORLD")

    # Resource tree creation
    root = resource.Site()  # Create the root resource site
    sensor = resource.Site() # Create a separate resource site for sensor data

    # Add resources to the root site
    root.add_resource(
        [".well-known", "core"], resource.WKCResource(root.get_resources_as_linkheader)
    )
    root.add_resource([], Welcome())
    root.add_resource(["time"], TimeResource())
    root.add_resource(["other", "block"], BlockResource())
    root.add_resource(["other", "separate"], SeparateLargeResource())
    root.add_resource(["whoami"], WhoAmI())
    # root.add_resource([''], AllResourcesHandler())  # Example of adding a handler for all resources

    # Add resources to the sensor site
    sensor.add_resource(['data'], AllResourcesHandler())  # Add a data resource to the sensor site
    root.add_resource(['sensor'], sensor)  # Add the sensor site to the root site

    # Create and bind the CoAP server context to the specified address and port
    await aiocoap.Context.create_server_context(root, bind=('0.0.0.0', 5683))

    # Run the event loop forever
    await asyncio.get_running_loop().create_future()

# Entry point for the script
if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())