#!/usr/bin/env python

# WSS (WS over TLS) server example, with a self-signed certificate

import asyncio
import pathlib
import ssl
import websockets

async def hello(websocket, path):
    name = await websocket.recv()
    print(f"< {name}")

    greeting = f"Hello {name}!"

    await websocket.send(greeting)
    print(f"> {greeting}")

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
crt = pathlib.Path("/home/ysh8361/workspace/webrtc/webrtc-tutorial/public.crt")
key = pathlib.Path("/home/ysh8361/workspace/webrtc/webrtc-tutorial/private.key")

ssl_context.load_cert_chain(crt, key)

start_server = websockets.serve(
    hello, "0.0.0.0", 9002, ssl=ssl_context
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()