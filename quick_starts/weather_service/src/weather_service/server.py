import os
import json
import logging
from tkinter import Image
import httpx
from datetime import datetime
from typing import Any, List, Dict
from dotenv import load_dotenv

from mcp.server.stdio import stdio_server
from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
from pydantic import AnyUrl

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("weather-server")

# API 설정
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise ValueError("OPENWEATHER_API_KEY 환경 변수가 설정되지 않았습니다.")


API_BASE_URL = "http://api.openweathermap.org/data/2.5"
DEFAULT_CITY = "Seoul"


## 날씨 정보 가져오기
http_parms = {
    "appid": API_KEY,
    "units": "metric",
}


async def fetch_weather(city: str) -> Dict[str, Any]:
    """지정된 도시의 현재 날씨 정보를 가져온다."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/weather",
            params={"q": city, **http_parms},
        )
        response.raise_for_status()
        
        data = response.json()
    
    return {
        "temperature": data["main"]["temp"],
        "conditions": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"],
        "timestamp": datetime.now().isoformat(),
    }

app = Server("weather-server")


## 리소스 핸들러 구현
@app.list_resources()
async def list_resources() -> List[Resource]:
    """사용 가능한 날씨 리소스를 나열"""
    uri = AnyUrl(f"weather://{DEFAULT_CITY}/current")
    return [
        Resource(
            uri=uri,
            name=f"{DEFAULT_CITY}의 현재 날씨",
            mimeType="application/json",
            description="실시간 날씨 데이터",
        )
    ]

@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """도시의 현재 날씨 데이터를 읽습니다"""
    if str(uri).startswith("weather://") and str(uri).endswith("/current"):
        city = str(uri).split("/")[-2]
    else:
        raise ValueError(f"지원되지 않는 URI: {uri}")
    

    try:
        weather_data = await fetch_weather(city)
        return json.dumps(weather_data, indent=2)
    except Exception as e:
        logger.error(f"날씨 데이터 가져오기 실패: {str(e)}")
        raise ValueError(f"날씨 데이터 가져오기 실패: {str(e)}")


## 도구 핸들러 구현
@app.list_tools()
async def list_tools() -> List[Tool]:
    """사용 가능한 날씨 관련 도구들을 나열합니다"""
    return [
        Tool(
            name="get_forecast",
            description="도시의 날씨 예보를 가져옵니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "도시 이름",
                    },
                    "days": {
                        "type": "number",
                        "description": "예보 일수(1-5)",
                        "minimum": 1,
                        "maximum": 5,
                    }
                },
                "required": ["city"],
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent | ImageContent | EmbeddedResource]:
    """날씨 예보 도구를 호출합니다"""
    if "get_forecast" != name:
        raise ValueError(f"지원되지 않는 도구: {name}")
    
    if not isinstance(arguments, dict) or "city" not in arguments:
        raise ValueError("도시 이름이 필요합니다")
    
    city = arguments["city"]
    days = min(int(arguments.get("days", 3)), 5)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/forecast",
                params={
                    "q": city,
                    "cnt": days * 8,
                    **http_parms
                },
            )
            response.raise_for_status()
            data = response.json()

        forecasts = []
        for i in range(0, len(data["list"]), 8):
            day_data = data["list"][i]
            forecasts.append({
                "date": day_data["list"][i],
                "temperature": day_data["main"]["temp"],
                "conditions": day_data["weather"][0]["description"],
            })

        return [
            TextContent(
                type="text",
                text=json.dumps(forecasts, indent=2),
            )
        ]

    except httpx.HTTPError as e:
        logger.error(f"날씨 API 오류: {str(e)}")
        raise RuntimeError(f"날씨 API 오류: {str(e)}")


## 서버 실행 코드
async def main():
    """서버 실행 메인 함수"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )






