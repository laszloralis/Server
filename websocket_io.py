import asyncio
import websockets
import json

import protocol_io as p_io


# #########################################################################
# Websocket I/O
# #########################################################################
TIMEOUT = 600.00  # sec

clients = set()


# =========================================================================
def clients_event():
    return json.dumps({"type": "clients", "count": len(clients)})


# =========================================================================
async def notify_clients():
    if clients:  # asyncio.wait doesn't accept an empty list
        message = clients_event()
        # await asyncio.wait([client.send(message) for client in clients])
        try:
            [await client.send(message) for client in clients]
        except websockets.WebSocketException as error:
            print("Websocket IO Error: ", error)


# =========================================================================
async def register(websocket):
    clients.add(websocket)
    await notify_clients()
    print(websocket, 'is registered and opened')


# =========================================================================
async def unregister(websocket):
    clients.remove(websocket)
    await websocket.close()
    await notify_clients()
    print(websocket, 'is unregistered and closed')


# =========================================================================
# handler
# =========================================================================
async def handler(websocket, path):
    # register(websocket) sends client_event() to websocket
    await register(websocket)

    try:
        while True:
            message = await asyncio.wait_for(websocket.recv(), TIMEOUT)
            print('message:', message)

            # Let the protocol process the received message and return an answer
            # see protocol_io.py for details
            answer = p_io.protocol_object.process_message(message)
            if answer is not None:
                print('answer :', answer)
                # send the answer to the client
                await websocket.send(answer)

            # sleep, to allow other message loops to do their jobs...
            await asyncio.sleep(0.250)

    except websockets.WebSocketException as error:
        print("Websocket io error: ", error)
    except asyncio.TimeoutError as error:
        print("Websocket timeout: ", error)
    finally:
        await unregister(websocket)


# =========================================================================
# broadcast()
# =========================================================================
def broadcast():
    if clients:
        message = p_io.protocol_object.get_broadcast_message()
        websockets.broadcast(clients, message)


# =========================================================================
# server(post_lock)
# =========================================================================
def infinite_io_loop():
    loop = asyncio.get_event_loop()
    start_server = websockets.serve(handler, "localhost", 8000)
    loop.run_until_complete(start_server)
    loop.run_forever()
