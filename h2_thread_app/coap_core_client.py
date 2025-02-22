import asyncio
import aiocoap
import logging

# Enable debug logging
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.WARNING)

"""
fdd5:419b:99e7:1:5656:d596:4ac8:7ccb --- Besprechungsraum
fdd5:419b:99e7:1:adeb:2df7:b87d:2bbc --- Roboterlabor
fdd5:419b:99e7:1:5656:d596:4ac8:7ccb --- UIC
fdd5:419b:99e7:1:92c6:f65f:4790:d24a --- Raum 1.08
"""


async def get_coap_core():
    uri = "coap://[fdd5:419b:99e7:1:5656:d596:4ac8:7ccb]:5683/temperature"
    context = await aiocoap.Context.create_client_context()

    try:
        # Create a GET request message
        request = aiocoap.Message(code=aiocoap.GET, uri=uri)
        print(f"Sending GET request to: {uri}")

        # Send the request and wait for any response
        response = await asyncio.wait_for(context.request(request).response, timeout=10)

        # Log the response
        print("Response Code:", response.code)
        print("Payload:", response.payload.decode('utf-8'))

    except asyncio.TimeoutError:
        print("Request timed out. The server did not respond in time.")
    except Exception as e:
        print("Error during CoAP request:", e)
    finally:
        # Shutdown the context
        await context.shutdown()

if __name__ == "__main__":
    asyncio.run(get_coap_core())
