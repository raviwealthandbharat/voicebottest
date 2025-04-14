import asyncio
import websockets

async def test_ws():
    uri = "wss://voicebottest.onrender.com"
    async with websockets.connect(uri) as websocket:
        with open("sample.pcm", "rb") as f:
            audio = f.read()
            await websocket.send(audio)
            reply_audio = await websocket.recv()
            with open("reply.pcm", "wb") as out:
                out.write(reply_audio)

asyncio.run(test_ws())
