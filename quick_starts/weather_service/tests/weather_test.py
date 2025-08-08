# tests/weather_test.py
import pytest
import os
from unittest.mock import patch, Mock
from datetime import datetime
import json
from pydantic import AnyUrl

os.environ["OPENWEATHER_API_KEY"] = "TEST"

from weather_service.server import (
    fetch_weather,
    read_resource,
    call_tool,
    list_resources,
    list_tools,
    DEFAULT_CITY
)

@pytest.fixture
def mock_weather_response():
    return {
        "main": {
            "temp": 20.5,
            "humidity": 65
        },
        "weather": [
            {"description": "scattered clouds"}
        ],
        "wind": {
            "speed": 3.6
        }
    }

@pytest.mark.anyio
async def test_fetch_weather(mock_weather_response):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        weather = await fetch_weather("Seoul")

        assert weather["temperature"] == 20.5
        assert weather["conditions"] == "scattered clouds"
        assert weather["humidity"] == 65
        assert weather["wind_speed"] == 3.6
        assert "timestamp" in weather