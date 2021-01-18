import asyncio
import json


async def iterable_to_async_iterable(iterable):
    for value in iterable:
        yield value


class Stream:

    def __init__(self, chunks=b''):
        if isinstance(chunks, bytes):
            chunks = [chunks]
        if not hasattr(chunks, '__aiter__'):
            chunks = iterable_to_async_iterable(chunks)
        self._cache = []
        self._chunks = chunks.__aiter__()

    async def chunks(self):
        index = 0
        while True:
            if index < len(self._cache):
                task = self._cache[index]
            else:
                task = asyncio.create_task(self._chunks.__anext__())
                self._cache.append(task)
            try:
                yield await task
            except StopAsyncIteration:
                break
            index += 1

    async def body(self):
        chunks = []
        async for chunk in self.chunks():
            chunks.append(chunk)
        return b''.join(chunks)

    async def text(self):
        return (await self.body()).decode()

    async def json(self):
        return json.loads(await self.body())
