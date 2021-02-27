from abc import ABC, abstractmethod
import asyncio
import json
import os
import urllib.parse

import aiofiles

from ..multidict import MultiDict
from ..parse import parse_content_type
from .. import multipart


async def iterable_to_async_iterable(iterable):
    for value in iterable:
        yield value


class SendFile:

    def __init__(self, path, *, offset=0, size=-1):
        self.path = os.fspath(path)
        self.offset = offset
        self.size = size

    async def chunks(self, *, chunk_size=4096):
        async with aiofiles.open(self.path, 'rb') as f:
            if self.offset != 0:
                await f.seek(self.offset)
            if chunk_size < 0:
                yield await f.read(self.size)
                return
            size = self.size
            while size != 0:
                chunk = await f.read(
                    chunk_size if size < 0 else min(chunk_size, size)
                )
                if not chunk:
                    break
                size -= len(chunk)
                yield chunk


class Stream(ABC):

    def __init__(self, chunks=b''):
        if isinstance(chunks, bytes):
            chunks = [chunks]
        if not hasattr(chunks, '__aiter__'):
            chunks = iterable_to_async_iterable(chunks)
        self._cache = []
        self._chunks = chunks.__aiter__()

    async def chunks(self, *, expand_files=True):
        index = 0
        while True:
            if index < len(self._cache):
                task = self._cache[index]
            else:
                task = asyncio.ensure_future(self._chunks.__anext__())
                self._cache.append(task)
            try:
                chunk = await task
            except StopAsyncIteration:
                break
            if isinstance(chunk, SendFile) and expand_files:
                async for chunk in chunk.chunks():
                    yield chunk
            else:
                yield chunk
            index += 1

    async def body(self):
        chunks = []
        async for chunk in self.chunks():
            chunks.append(chunk)
        return b''.join(chunks)

    async def text(self):
        return (await self.body()).decode(self.charset)

    async def json(self):
        return json.loads(await self.body())

    async def form(self):
        if self.content_type == 'application/x-www-form-urlencoded':
            return MultiDict(urllib.parse.parse_qsl(await self.text()))
        elif self.content_type == 'multipart/form-data':
            return multipart.parse(await self.body(), boundary=self.boundary)
        else:
            raise ValueError(
                'content type must be either '
                'application/x-www-form-urlencoded or multipart/form-data, '
                f'not {self.content_type}'
            )

    @abstractmethod
    def _get_content_type(self):
        raise NotImplementedError

    @property
    def content_type(self):
        content_type, _ = parse_content_type(self._get_content_type())
        return content_type

    @property
    def charset(self):
        _, params = parse_content_type(self._get_content_type())
        return params.get('charset', 'UTF-8')

    @property
    def boundary(self):
        _, params = parse_content_type(self._get_content_type())
        try:
            return params['boundary']
        except KeyError:
            raise ValueError('no boundary provided') from None
