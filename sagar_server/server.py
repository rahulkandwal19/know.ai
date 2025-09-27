# Importing Required Modules
import json
import uuid
import asyncio
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

#Initilization of FastAPI Server
app = FastAPI()

#------------------------------------------------------------------------------------------
# ConnectionManages : It is utilize to create and manage multiple WEB-SOCKET connections 
# between server and client. It is responsible to keep track of connections in dictionary, 
# create new connections , accept request, manage disconnects and send message to client.

class ConnectionManager:

    # Manage connections in dictionary {connection_id : WEBSOCKET}
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    # Accept new requests and create connections
    async def connect(self, websocket: WebSocket):
        connection_id = str(uuid.uuid4())
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        return connection_id

    # Clear connection from dictionary on client disconnected
    def disconnect(self, connection_id: str):
        self.active_connections.pop(connection_id, None)

    # Send message to client over the WEB-Socket connection
    async def send_to_client(self, connection_id: str, message: str):
        CLIENT_CONNECTION = self.active_connections.get(connection_id)
        if CLIENT_CONNECTION:
            await CLIENT_CONNECTION.send_text(message)


# Instance for managing connections 
manager = ConnectionManager()

#------------------------------------------------------------------------------------------

# Sends Heatbeat Messages to keep the connection live and prevent from timeouts
async def send_heartbeat(connection_id: str, interval: int = 30):
    while True:
        await asyncio.sleep(interval)
        try:
            await manager.send_to_client(connection_id, '{"type":"heartbeat"}')
        except WebSocketDisconnect:
            break


# Connect with LLM Server (SagarTinyAI) and stream tokes as genereted  
async def generate_sagarAI_tiny(context: str,question: str):
    URI = "ws://model-server-sagar-tiny:8001/generate"
    try:
        async with websockets.connect(URI) as LLM_CONNECTION:
            await LLM_CONNECTION.send(json.dumps({
                "context": context,
                "question": question
            }))

            async for message in LLM_CONNECTION:
                try:
                    token = json.loads(message)
                    yield token
                except json.JSONDecodeError:
                    yield {"type": "token", "message": message}

    except Exception as e:
        yield {"type": "error", "message": str(e)}

#------------------------------------------------------------------------------------------
@app.get("/")
async def test_interface():
    return FileResponse("testClient.html")

# API Endpoint : test - echo the message of client used for checking server is live  
@app.websocket("/test")
async def test(websocket: WebSocket):
    client_id = await manager.connect(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            print(f" [{client_id}] Received: {message}")
            await manager.send_to_client(client_id, f'{{"type":"echo","message":"{message}"}}')
    finally:
        manager.disconnect(client_id)


# API Endpoint : sagarAI - used to get answer of clients prompt form default sagarAI model
@app.websocket("/sagarAI")
async def sagar_ai(websocket: WebSocket):
    client_id = await manager.connect(websocket) 

    # Add heartbeats in connection to keep connection live 
    heartbeat_task = asyncio.create_task(send_heartbeat(client_id))

    try:
        while True:
            try:
                question = await asyncio.wait_for(websocket.receive_text(), timeout=300)
                context = "Exploring about Indian EEZ, ocean scientific surver and marine studies"
            except asyncio.TimeoutError:
                await manager.send_to_client(client_id, '{"type":"timeout","message":"Idle Till 300Sec"}')
                continue
            
            try:
                async for chunk in generate_sagarAI_tiny(context,question):
                    await manager.send_to_client(client_id, json.dumps(chunk))
                await manager.send_to_client(client_id, '{"type":"done","message":"done"}')
            except Exception as e:
                await manager.send_to_client(client_id, f'{{"type":"error","message":"{str(e)}"}}')
    finally:
        heartbeat_task.cancel()
        manager.disconnect(client_id)
#------------------------------------------------------------------------------------------
