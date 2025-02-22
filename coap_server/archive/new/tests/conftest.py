import pytest

@pytest.fixture
def sample_payload():
    """Sample sensor payload."""
    return {
        "device": "3a:4f:ec:85:c0:65:36:19",
        "temperature": 25.5,
        "humidity": 60,
        "neighbor_rssi": [
            {"MAC": "8e:d0:82:0b:a8:e5:c8:93", "RSSI": -70}
        ]
    }
