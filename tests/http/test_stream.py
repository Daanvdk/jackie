import asyncio
import pytest

from jackie.http.stream import Stream


# Very simple stream implementation that allows us to specify the content type

class ContentTypeStream(Stream):

    def __init__(self, body=b'', content_type='text/plain; charset=UTF-8'):
        super().__init__(body)
        self._content_type = content_type

    def _get_content_type(self):
        return self._content_type


@pytest.mark.asyncio
async def test_async_chunks_to_chunks():
    async def async_chunks():
        yield b'foo'
        yield b'bar'
    stream = ContentTypeStream(async_chunks())
    chunks = []
    async for chunk in stream.chunks():
        chunks.append(chunk)
    assert chunks == [b'foo', b'bar']


@pytest.mark.asyncio
async def test_chunks_to_chunks():
    def chunks():
        yield b'foo'
        yield b'bar'
    stream = ContentTypeStream(chunks())
    chunks = []
    async for chunk in stream.chunks():
        chunks.append(chunk)
    assert chunks == [b'foo', b'bar']


@pytest.mark.asyncio
async def test_bytes_to_chunks():
    stream = ContentTypeStream(b'foobar')
    chunks = []
    async for chunk in stream.chunks():
        chunks.append(chunk)
    assert chunks == [b'foobar']


@pytest.mark.asyncio
async def test_async_chunks_to_body():
    async def async_chunks():
        yield b'foo'
        yield b'bar'
    stream = ContentTypeStream(async_chunks())
    body = await stream.body()
    assert body == b'foobar'


@pytest.mark.asyncio
async def test_chunks_to_body():
    def chunks():
        yield b'foo'
        yield b'bar'
    stream = ContentTypeStream(chunks())
    body = await stream.body()
    assert body == b'foobar'


@pytest.mark.asyncio
async def test_bytes_to_body():
    stream = ContentTypeStream(b'foobar')
    body = await stream.body()
    assert body == b'foobar'


@pytest.mark.asyncio
async def test_async_chunks_to_text():
    async def async_chunks():
        yield b'foo'
        yield b'bar'
    stream = ContentTypeStream(async_chunks())
    text = await stream.text()
    assert text == 'foobar'


@pytest.mark.asyncio
async def test_chunks_to_text():
    def chunks():
        yield b'foo'
        yield b'bar'
    stream = ContentTypeStream(chunks())
    text = await stream.text()
    assert text == 'foobar'


@pytest.mark.asyncio
async def test_bytes_to_text():
    stream = ContentTypeStream(b'foobar')
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
    stream = ContentTypeStream(async_chunks())
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
    stream = ContentTypeStream(chunks())
    data = await stream.json()
    assert data == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_bytes_to_json():
    stream = ContentTypeStream(b'{"foo": "bar"}')
    data = await stream.json()
    assert data == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_stream_multiple_chunks():
    stream = ContentTypeStream([b'foo', b'bar', b'baz'])
    chunks1 = stream.chunks()
    chunks2 = stream.chunks()

    chunk1 = await chunks1.__anext__()
    chunk2 = await chunks2.__anext__()

    assert chunk1 == b'foo'
    assert chunk2 == b'foo'

    chunk1 = asyncio.ensure_future(chunks1.__anext__())
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


@pytest.mark.asyncio
async def test_parse_form_multipart():
    stream = ContentTypeStream(
        body=(
            b'--boundary\n'
            b'Content-Disposition: form-data; name=foo\n'
            b'\n'
            b'123\n'
            b'--boundary\n'
            b'Content-Disposition: form-data; name=bar\n'
            b'\n'
            b'456\n'
            b'--boundary\n'
            b'Content-Disposition: form-data; name=baz\n'
            b'\n'
            b'789\n'
            b'--boundary--\n'
        ),
        content_type='multipart/form-data; boundary=boundary',
    )
    assert await stream.form() == {
        'foo': '123',
        'bar': '456',
        'baz': '789',
    }


@pytest.mark.asyncio
async def test_parse_form_urlencoded():
    stream = ContentTypeStream(
        body=b'foo=123&bar=456&baz=789',
        content_type='application/x-www-form-urlencoded',
    )
    assert await stream.form() == {
        'foo': '123',
        'bar': '456',
        'baz': '789',
    }


@pytest.mark.asyncio
async def test_parse_form_incorrect_content_type():
    stream = ContentTypeStream(
        body=b'foo=123&bar=456&baz=789',
        content_type='',
    )
    with pytest.raises(ValueError):
        await stream.form()


def test_parse_no_content_type():
    stream = ContentTypeStream(content_type=None)
    assert stream.content_type is None
    assert stream.charset == 'UTF-8'
    with pytest.raises(ValueError):
        stream.boundary


def test_parse_content_type_with_charset():
    stream = ContentTypeStream(content_type='text/plain; charset=foo')
    assert stream.content_type == 'text/plain'
    assert stream.charset == 'foo'
    with pytest.raises(ValueError):
        stream.boundary


def test_parse_content_type_without_charset():
    stream = ContentTypeStream(content_type='text/plain')
    assert stream.content_type == 'text/plain'
    assert stream.charset == 'UTF-8'
    with pytest.raises(ValueError):
        stream.boundary


def test_parse_content_type_with_boundary():
    stream = ContentTypeStream(
        content_type='multipart/form-data; boundary=foo',
    )
    assert stream.content_type == 'multipart/form-data'
    assert stream.charset == 'UTF-8'
    assert stream.boundary == 'foo'
