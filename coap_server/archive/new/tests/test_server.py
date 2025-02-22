import pytest
from unittest.mock import patch, AsyncMock
import asyncio
from src.server import CoAPServer

@pytest.fixture
async def coap_server():
    server = CoAPServer()
    await server.mqtt_handler.connect()  # Ensure connection before yielding
    yield server
    await server.mqtt_handler.stop()

@patch('aiocoap.Context.create_server_context')
@pytest.mark.asyncio
async def test_server_startup(mock_context):
    server = CoAPServer()
    
    # Mock MQTT handler methods
    server.mqtt_handler.connect = AsyncMock(return_value=True)
    server.mqtt_handler.start = AsyncMock()
    
    # Start server
    task = asyncio.create_task(server.start())
    await asyncio.sleep(0.1)
    task.cancel()
    
    # Verify calls
    assert mock_context.called
    assert server.mqtt_handler.connect.called
    assert server.mqtt_handler.start.called
