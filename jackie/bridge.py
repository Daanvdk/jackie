import asyncio


def bridge():
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue()

    async def send(message):
        receiver = await queue.get()
        receiver.set_result(message)

    async def receive():
        receiver = loop.create_future()
        await queue.put(receiver)
        return await receiver

    return send, receive
