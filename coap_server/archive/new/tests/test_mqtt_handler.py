import pytest
from unittest.mock import patch, MagicMock
from src.mqtt_handler import MQTTHandler

@pytest.fixture
def mqtt_handler():
    return MQTTHandler()

def test_mqtt_handler_init(mqtt_handler):
    assert mqtt_handler.client is not None
    assert mqtt_handler.logger is not None

@patch('paho.mqtt.client.Client')
@pytest.mark.asyncio
async def test_mqtt_connect_success(mock_client):
    handler = MQTTHandler()
    handler.client = mock_client
    mock_client.connect.return_value = 0
    
    assert await handler.connect() is True
    mock_client.connect.assert_called_once()

@patch('paho.mqtt.client.Client')
@pytest.mark.asyncio
async def test_mqtt_publish_success(mock_client):
    handler = MQTTHandler()
    handler.client = mock_client
    mock_client.publish.return_value = (0, 0)  # (rc, mid)
    
    assert await handler.publish("test/topic", "test_payload") is True
    mock_client.publish.assert_called_with(topic="test/topic", payload="test_payload")

@patch('paho.mqtt.client.Client')
@pytest.mark.asyncio
async def test_start_stop(mock_client_class):
    # Setup
    handler = MQTTHandler()
    mock_client = MagicMock()
    handler.client = mock_client
    
    # Test start
    await handler.start()
    mock_client.loop_start.assert_called_once()
    
    # Test stop
    await handler.stop()
    mock_client.loop_stop.assert_called_once()
