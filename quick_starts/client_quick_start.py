import asyncio
from typing import Optional

# 비동기 컨텍스트 매니저를 중첩해서 사용할 수 있게 해주는 유틸리티
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()


# 기본 클라이언트 구조
# (https://modelcontextprotocol.io/quickstart/client)
class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()

    # 서버 연결 관리
    async def connect_to_server(self, server_script_path: str):
        """
        Connect to an MCP server

        Args:
            server_script_path: Path to the MCP server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError(
                f"Server script must be a .py or .js file, got {server_script_path}"
            )

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,  # 서버 실행에 사용할 명령어 (python 또는 node)
            args=[server_script_path],  # 서버 스크립트 경로를 포함한 실행 인자 목록
            env=None,  #  서버 프로세스에 전달할 환경 변수 (None인 경우 현재 프로세스의 환경 변수 상속)
        )

        # stdio_client()를 사용하여 서버와의 표준 입출력 기반 통신 채널을 생성
        # AsyncExitStack을 통해 컨텍스트 관리자로 등록하여 자원을 안전하게 관리
        # stdio_transport: 생성된 통신 채널을 나타내는 transport 객체 반환
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        # stdio_transport에서 읽기/쓰기 스트림을 분리하여 각각 저장
        self.stdio, self.write = stdio_transport

        # ClientSession 객체를 생성하고 AsyncExitStack에 등록
        # - stdio: 서버로부터 데이터를 읽는 스트림
        # - write: 서버로 데이터를 쓰는 스트림
        # 세션이 생성되면 서버와의 양방향 통신이 가능해짐
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print(f"Available tools: {(', '.join([tool.name for tool in tools]))}")
