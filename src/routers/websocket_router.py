import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

from src.services.websocket import ConnectionManager

websocket_router = APIRouter(prefix='/ws', tags=['WebSocket'])

manager = ConnectionManager()

@websocket_router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            
            event_type = data.get("event")
            payload = data.get("message", "")

            if payload != "":

                if event_type == "notification":
                    await manager.broadcast(
                        {
                            "event": "Nueva notificación", 
                            "message": payload,
                        }
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# @websocket_router.websocket("/")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_json()
#             print(data)
#             # Enviar un mensaje cada 5 minutos (300 segundos)
#             await asyncio.sleep(5)
#             await websocket.send_json(
#                 {"event": "alert", "message": "Actualizacion del ws!!!!", "hola pepe": " hola pepe", "como te va?" : "rica papa, te voy a dar"}
#             )

#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
