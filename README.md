## Concepts of MCP
- 아래의 개념 정리는 [MCP Docs](https://modelcontextprotocol.io/docs/learn/architecture) 를 참고하였음.

### Overview
- MCP는 AI 모델에 Context를 제공하기 위한 프로토콜
- MCP는 Context 전달을 위한 Protocol 자체에만 집중하며,<br>
  AI App이 LLM을 어떻게 사용하거나 전달받은 컨텍스트를 어떻게 처리하는지 규정하지 않는다.
- 개발자는 보통 Data Layer Protocol에 집중하면 된다.  
  (실제 구현은 각 언어별 SDK 문서를 참조)

### Participants
- MCP는 Client-Server Archtecture를 따른다.
- MCP Host는 하나 이상의 MCP Server와 연결하며,<br>
  각 서버마다 하나의 MCP Client를 생성함.
- MCP Client는 해당 MCP Server와 1:1 전용 연결을 유지한다.
- 주요 구성요소
  - **MCP Host:** AI Application 자체 (하나 이상의 MCP CLient를 생성 및 관리)
  - **MCP Client:** MCP Server와의 연결을 유지하고 Context를 가져오는 Component (Host를 대신해 Server와 통신하며 Context를 획득)
  - **MCP Server:** MCP Cient에 context를 제공하는 프로그램 (파일 시스템, Sentry, DB 등에서 데이터를 제공할 수 있음)

<p align="center">
  <img width="702" height="295" alt="image" src="https://github.com/user-attachments/assets/061093a4-6564-4981-8ac5-a0a180db1ccc" />
</p>

<br>

- MCP 서버는 Local 또는 Remote 환경에서 실행될 수 있다.
  - Local MCP Server
    - Claude Desktop이 파일 시스템을 실행할 떄,<br>
      이 Server는 같은 컴퓨터에서 ```STDIO``` 방식을 사용하여 실행된다.
    - 이를 **로컬 MCP Server**라고 부른다.

  - Remote MCP Server
    - 공식 Sentry MCP Server는 Sentry Platform 상에서 실행되며, ```Streamable HTTP``` 전송 방식을 사용한다.
    - 이를 **원격 MCP Server**라고 부른다.

- 실행 위치는 다르더라도 MCP 서버의 본질적인 역할은 **Client에게 Context 데이터를 제공하는 것**이다.

### Layers
- MCP는 두 개의 계층으로 구성된다. <br>

  **1. Data Layer**
    - JSON-RPC 기반의 Client-Server 통신 프로토콜을 정의
    - 주요 기능
      - 연결 수명 주기 관리 (lifecycle management)
        - **MCP는 상태를 유지하는 프로토콜(Stateful Protocol)** 이다.
        - 클라이언트-서버 간 연결 초기화
        - 기능 협상 (capability negotiation)
        - 연결 종료 처리
      - Server Features
        - ```tools```: AI Action을 위한 기능 제공
        - ```resources```: 컨텍스트 데이터를 제공
        - ```prompts```: 상호작용 템플릿 전달
      - Client Features
        - 서버가 클라이언트에 요청 가능
          - LLM 샘플링 요청 (예: AI 응답 생성)
          - 사용자 입력 유도
          - 클라이언트 측 로그 기록
      - Utility Features
        - ```notifications```: 실시간 알림, 장시간 작업의 진행 상태 추적
    - **MCP 기능이 핵심 로직이 담긴 내부 계층 (inner layer)**

  <br>

  **2. Transport Layer**
    - **Client와 Server 간의 데이터 송수신 및 인증 처리**를 담당
      - 연결 수립 (Connection Establishment)
      - 메시지 프레이밍 (Message Framing)
      - 안전한 통신 및 인증
    - MCP는 두 가지 전송 방식을 지원
      1. Stdio Transport
         - 표준 입력/출력을 사용
         - 동일 머신 내 프로세스 간 직접 통신
         - 네트워크 오버헤드 없음 → 최고 성능
      2. Streamable HTTP Transport
         - 클라이언트 서버: ```HTTP POST```
         - 서버 → 클라이언트: SSE(Server-Sent Events) 사용 가능
         - 원격 서버와 통신 가능
         - 인증: Bearer Token, API Key, 커스텀 헤더 등 지원
         - MCP 권장 인증 방식: **OAuth**
    - 전송 계층은 프로토콜 계층과 분리되어 있으며, 어떤 전송 방식을 사용해도<br> 동일한 JSON-RPC 2.0 메시지 형식을 사용할 수 있도록 추상화되어 있음    
    - 데이터 전달을 위한 **외부 계층 (outer layer)**

 <br>

<p align="center">
<img width="417" height="141" alt="image" src="https://github.com/user-attachments/assets/8f5a76d3-1992-44a6-8eb8-1c7e8dac1def" />
</p>

- MCP 서버가 제공하는 핵심 기본요소
  <p align="left">
    <img width="555" height="162" alt="image" src="https://github.com/user-attachments/assets/bd2fb908-4ba7-491d-b821-784865d4b79b" />
  </p>

- MCP 클라이언트가 제공할 수 있는 기본요소
  <p align="left">
    <img width="518" height="204" alt="image" src="https://github.com/user-attachments/assets/2fd8fe92-b5ff-494c-8348-9424bad9d950" />
  </p>


### Notifications
- MCP는 실시간 알림 기능 지원
- 서버와 클라이언트 간의 동적 업데이트를 가능하게 함

- 사용 목적
  - 서버에서 사용 가능한 tools 목록이 변경되었을 때<br>
    서버는 클라이언트에게 변경 사항을 즉시 알릴 수 있음
  - 클라이언트는 이에 따라 UI를 업데이트하거나, 새로운 동작을 지원
 
- 전송 방식
  - JSON-RPC 2.0의 Notification 메시지 형식으로 전송됨
  - 응답을 기대하지 않는 단방향 메시지 (request와 다름)
  - 서버 → 클라이언트 방향으로 비동기 이벤트 알림
