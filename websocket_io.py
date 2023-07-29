import asyncio
import websockets


# #########################################################################
# Websocket I/O
# #########################################################################
class WebsocketIO:
    # TODO - Timeout for Client communication
    #  - currently the clients should answer to the broadcast messages
    #    (for development purposes)
    #  - this behavior can be changed in the future
    #    (in this case timeout will be not needed anymore)
    TIMEOUT = 600.00  # sec

    # =========================================================================
    def __init__(self, protocol_callback_fn):
        self.__TIMEOUT = 600.00  # sec
        self.__clients = set()
        self.__protocol_callback_fn = protocol_callback_fn

    # =========================================================================
    def start_server(self):
        loop = asyncio.get_event_loop()
        start_server = websockets.serve(self.__handler, "localhost", 8000)
        loop.run_until_complete(start_server)
        loop.run_forever()

    # =========================================================================
    def get_client_count(self):
        return len(self.__clients)

    # =========================================================================
    def broadcast(self, message):
        if self.__clients:
            websockets.broadcast(self.__clients, message)

    # =========================================================================
    async def __register(self, websocket):
        self.__clients.add(websocket)
        # await notify_clients()
        print(f'WebsocketIO: \'{websocket}\' is registered and opened')

    # =========================================================================
    async def __unregister(self, websocket):
        self.__clients.remove(websocket)
        await websocket.close()
        # await notify_clients()
        print(f'WebsocketIO: \'{websocket}\' is unregistered and closed')

    # =========================================================================
    async def __handler(self, websocket, path):
        # register(websocket) sends client_event() to websocket
        await self.__register(websocket)

        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), WebsocketIO.TIMEOUT)

                print('message:', message)

                # Let the protocol process the received message and return an answer
                # see protocol_io.py for details
                answer = self.__protocol_callback_fn(message)
                if answer is not None:
                    # send the answer to the client
                    await websocket.send(answer)

                    print('answer :', answer)

                # sleep, to allow other message loops to do their jobs...
                await asyncio.sleep(0.250)

        except websockets.WebSocketException as error:
            print("WebsocketIO io error: ", error)
        except asyncio.TimeoutError as error:
            print("WebsocketIO timeout: ", error)
        finally:
            await self.__unregister(websocket)
