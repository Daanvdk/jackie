import asyncio
import pytest

from jack.http.stream import Stream


@pytest.mark.asyncio
async def test_async_chunks_to_chunks():
    async def async_chunks():
        yield b'foo'
        yield b'bar'
    stream = Stream(async_chunks())
    chunks = []
    async for chunk in stream.chunks():
        chunks.append(chunk)
    assert chunks == [b'foo', b'bar']


@pytest.mark.asyncio
async def test_chunks_to_chunks():
    def chunks():
        yield b'foo'
        yield b'bar'
    stream = Stream(chunks())
    chunks = []
    async for chunk in stream.chunks():
        chunks.append(chunk)
    assert chunks == [b'foo', b'bar']


@pytest.mark.asyncio
async def test_bytes_to_chunks():
    stream = Stream(b'foobar')
    chunks = []
    async for chunk in stream.chunks():
        chunks.append(chunk)
    assert chunks == [b'foobar']


@pytest.mark.asyncio
async def test_async_chunks_to_body():
    async def async_chunks():
        yield b'foo'
        yield b'bar'
    stream = Stream(async_chunks())
    body = await stream.body()
    assert body == b'foobar'


@pytest.mark.asyncio
async def test_chunks_to_body():
    def chunks():
        yield b'foo'
        yield b'bar'
    stream = Stream(chunks())
    body = await stream.body()
    assert body == b'foobar'


@pytest.mark.asyncio
async def test_bytes_to_body():
    stream = Stream(b'foobar')
    body = await stream.body()
    assert body == b'foobar'


@pytest.mark.asyncio
async def test_async_chunks_to_text():
    async def async_chunks():
        yield b'foo'
        yield b'bar'
    stream = Stream(async_chunks())
    text = await stream.text()
    assert text == 'foobar'


@pytest.mark.asyncio
async def test_chunks_to_text():
    def chunks():
        yield b'foo'
        yield b'bar'
    stream = Stream(chunks())
    text = await stream.text()
    assert text == 'foobar'


@pytest.mark.asyncio
async def test_bytes_to_text():
    stream = Stream(b'foobar')
    text = await stream.text()
    assert text == 'foobar'


@pytest.mark.asyncio
async def test_async_chunks_to_json():
    async def async_chunks():
        yield b'{'
        yield b'"foo"'
        yield b': '
        yield b'"bar"'
        yield b'}'
    stream = Stream(async_chunks())
    data = await stream.json()
    assert data == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_chunks_to_json():
    def chunks():
        yield b'{'
        yield b'"foo"'
        yield b': '
        yield b'"bar"'
        yield b'}'
    stream = Stream(chunks())
    data = await stream.json()
    assert data == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_bytes_to_json():
    stream = Stream(b'{"foo": "bar"}')
    data = await stream.json()
    assert data == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_stream_multiple_chunks():
    stream = Stream([b'foo', b'bar', b'baz'])
    chunks1 = stream.chunks()
    chunks2 = stream.chunks()

    chunk1 = await chunks1.__anext__()
    chunk2 = await chunks2.__anext__()

    assert chunk1 == b'foo'
    assert chunk2 == b'foo'

    chunk1 = asyncio.create_task(chunks1.__anext__())
    chunk2 = await chunks2.__anext__()
    chunk1 = await chunk1

    assert chunk1 == b'bar'
    assert chunk2 == b'bar'

    chunk1 = await chunks1.__anext__()
    chunk2 = await chunks2.__anext__()

    assert chunk1 == b'baz'
    assert chunk2 == b'baz'

    with pytest.raises(StopAsyncIteration):
        await chunks1.__anext__()
    with pytest.raises(StopAsyncIteration):
        await chunks2.__anext__()
