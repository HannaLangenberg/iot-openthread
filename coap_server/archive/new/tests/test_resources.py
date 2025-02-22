import json
import pytest
from unittest.mock import MagicMock, PropertyMock
from aiocoap import Message, Code
from src.resources import MQTTBridgeResource

@pytest.fixture
def mqtt_handler():
    handler = MagicMock()
    handler.publish.return_value = True
    return handler

@pytest.fixture
def bridge_resource(mqtt_handler):
    return MQTTBridgeResource(mqtt_handler)

@pytest.mark.asyncio
async def test_resource_valid_payload(bridge_resource):
    payload = {
        "device": "3a:4f:ec:85:c0:65:36:19",
        "temperature": 25.5
    }
    
    # Create a properly mocked request
    request = MagicMock(spec=Message)
    request.payload = json.dumps(payload).encode()
    request.opt = MagicMock()
    request.opt.uri_path = ['sensor']
    
    # Mock get_request_uri method
    request.get_request_uri.return_value = "coap://localhost/sensor"
    
    # Set is_response property
    type(request).remote = PropertyMock(return_value=None)
    
    response = await bridge_resource.render(request)
    assert response.code == Code.CONTENT
    bridge_resource.mqtt_handler.publish.assert_called_once()

@pytest.mark.asyncio
async def test_resource_invalid_payload(bridge_resource):
    request = MagicMock(spec=Message)
    request.payload = b"invalid json"
    request.get_request_uri.return_value = "coap://localhost/sensor"
    type(request).remote = PropertyMock(return_value=None)
    
    response = await bridge_resource.render(request)
    assert response.code == Code.INTERNAL_SERVER_ERROR
