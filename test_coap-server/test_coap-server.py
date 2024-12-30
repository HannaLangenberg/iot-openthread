import unittest
import asyncio
from datetime import datetime

from aiocoap import Message, Code, ContentFormat
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coap_server.coap_server import AllResourcesHandler, Welcome, BlockResource, SeparateLargeResource, TimeResource, WhoAmI

class TestCoAPServer(unittest.TestCase):
    """
    Test suite for the CoAP server.
    """

    def setUp(self):
        """
        Set up the test environment by creating a new asyncio event loop.
        """
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """
        Tear down the test environment by closing the asyncio event loop.
        """
        self.loop.close()

    def test_all_resources_handler(self):
        """
        Test the AllResourcesHandler by sending a GET request and checking the response.
        """
        handler = AllResourcesHandler()
        request = Message(code=Code.GET, payload=b"Test payload", content_format=ContentFormat.TEXT)
        response = self.loop.run_until_complete(handler.render(request))
        self.assertEqual(response.code, Code.CONTENT)
        self.assertEqual(response.payload, b"Generic response for any resource")

    def test_welcome(self):
        """
        Test the Welcome handler by sending a GET request and checking the response.
        """
        handler = Welcome()
        request = Message(code=Code.GET, content_format=ContentFormat.TEXT)
        response = self.loop.run_until_complete(handler.render_get(request))
        self.assertEqual(response.payload, b"Welcome to the demo server")

    def test_block_resource(self):
        """
        Test the BlockResource handler by sending GET and PUT requests and checking the responses.
        """
        handler = BlockResource()
        request_get = Message(code=Code.GET, content_format=ContentFormat.TEXT)
        request_get.remote = type('Remote', (object,), {'hostinfo': 'localhost'})
        response_get = self.loop.run_until_complete(handler.render_get(request_get))
        self.assertEqual(len(response_get.payload), 1024)

        request_put = Message(code=Code.PUT, payload=b"New content", content_format=ContentFormat.TEXT)
        request_put.remote = type('Remote', (object,), {'hostinfo': 'localhost'})
        response_put = self.loop.run_until_complete(handler.render_put(request_put))
        self.assertEqual(response_put.code, Code.CHANGED)
        self.assertEqual(response_put.payload[:11], b"New content")

    def test_separate_large_resource(self):
        """
        Test the SeparateLargeResource handler by sending a GET request and checking the response.
        """
        handler = SeparateLargeResource()
        request = Message(code=Code.GET, content_format=ContentFormat.TEXT)
        request.remote = type('Remote', (object,), {'hostinfo': 'localhost'})
        response = self.loop.run_until_complete(handler.render_get(request))
        self.assertIn(b"Three rings for the elven kings", response.payload)

    def test_time_resource(self):
        """
        Test the TimeResource handler by sending a GET request and checking the response.
        """
        handler = TimeResource()
        request = Message(code=Code.GET, content_format=ContentFormat.TEXT)
        request.remote = type('Remote', (object,), {'hostinfo': 'localhost'})
        response = self.loop.run_until_complete(handler.render_get(request))
        self.assertIn(datetime.now().strftime("%Y-%m-%d"), response.payload.decode("ascii"))

    def test_whoami(self):
        """
        Test the WhoAmI handler by sending a GET request and checking the response.
        """
        handler = WhoAmI()
        request = Message(code=Code.GET, content_format=ContentFormat.TEXT)
        request.remote = type('Remote', (object,), {'scheme': 'coap', 'hostinfo': 'localhost', 'hostinfo_local': '127.0.0.1', 'authenticated_claims': []})
        response = self.loop.run_until_complete(handler.render_get(request))
        self.assertIn(b"Used protocol: coap.", response.payload)
        self.assertIn(b"Request came from localhost.", response.payload)
        self.assertIn(b"The server address used 127.0.0.1.", response.payload)

if __name__ == '__main__':
    unittest.main()