import asyncio
import urllib.parse
import tempfile

import pytest

from jackie.http import (
    asgi_to_jackie, jackie_to_asgi, Request, Response, Socket,
    Disconnect,
)
from jackie.http.stream import SendFile


@pytest.mark.asyncio
async def test_jackie_to_asgi():
    @jackie_to_asgi
    async def app(request):
        name = request.query.get('name', 'World')
        return Response(text=f'Hello, {name}!')

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(app(scope, input_queue.get, output_queue.put))

    message = await output_queue.get()
    assert message['type'] == 'http.response.start'
    assert message['status'] == 200
    assert message['headers'] == [
        (b'content-type', b'text/plain; charset=UTF-8'),
    ]

    body = b''
    while True:
        message = await output_queue.get()
        body += message['body']
        if not message['more_body']:
            break
    assert body == b'Hello, World!'

    await task

    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'query_string': b'name=Jack',
        'headers': [],
    }
    task = asyncio.ensure_future(app(scope, input_queue.get, output_queue.put))

    message = await output_queue.get()
    assert message['type'] == 'http.response.start'
    assert message['status'] == 200
    assert message['headers'] == [
        (b'content-type', b'text/plain; charset=UTF-8'),
    ]

    body = b''
    while True:
        message = await output_queue.get()
        body += message['body']
        if not message['more_body']:
            break
    assert body == b'Hello, Jack!'

    await task


@pytest.mark.asyncio
async def test_asgi_to_jackie():
    @asgi_to_jackie
    async def view(scope, receive, send):
        query = urllib.parse.parse_qs(scope['query_string'].decode())
        try:
            name = query['name'][-1]
        except KeyError:
            name = 'World'
        body = f'Hello, {name}!'.encode()
        await send({'type': 'http.response.start', 'status': 200, 'headers': [
            (b'content-type', b'text/plain; charset=UTF-8'),
        ]})
        await send({'type': 'http.response.body', 'body': body})

    response = await view(Request())
    assert response.status == 200
    assert list(response.headers.allitems()) == [
        ('content-type', 'text/plain; charset=UTF-8'),
    ]
    assert await response.body() == b'Hello, World!'

    response = await view(Request(query={'name': 'Jack'}))
    assert response.status == 200
    assert list(response.headers.allitems()) == [
        ('content-type', 'text/plain; charset=UTF-8'),
    ]
    assert await response.body() == b'Hello, Jack!'


def test_double_wrap():
    async def app(scope, receive, send):
        pass

    async def view(request):
        pass

    assert jackie_to_asgi(asgi_to_jackie(app)) is app
    assert asgi_to_jackie(jackie_to_asgi(view)) is view


@pytest.mark.asyncio
async def test_jackie_to_asgi_request_body():
    @jackie_to_asgi
    async def app(request):
        return Response(body=request.chunks())

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'query_string': b'name=Jack',
        'headers': [],
    }
    task = asyncio.ensure_future(app(scope, input_queue.get, output_queue.put))

    message = await output_queue.get()
    assert message['type'] == 'http.response.start'
    assert message['status'] == 200
    assert message['headers'] == []

    await input_queue.put({
        'type': 'http.request',
        'body': b'foo',
        'more_body': True,
    })
    assert await output_queue.get() == {
        'type': 'http.response.body',
        'body': b'foo',
        'more_body': True,
    }
    await input_queue.put({
        'type': 'http.request',
        'body': b'bar',
        'more_body': False,
    })
    assert await output_queue.get() == {
        'type': 'http.response.body',
        'body': b'bar',
        'more_body': True,
    }
    assert await output_queue.get() == {
        'type': 'http.response.body',
        'body': b'',
        'more_body': False,
    }

    await task

    task = asyncio.ensure_future(app(scope, input_queue.get, output_queue.put))

    message = await output_queue.get()
    assert message['type'] == 'http.response.start'
    assert message['status'] == 200
    assert message['headers'] == []

    await input_queue.put({'type': 'http.disconnect'})
    await task

    task = asyncio.ensure_future(app(scope, input_queue.get, output_queue.put))

    message = await output_queue.get()
    assert message['type'] == 'http.response.start'
    assert message['status'] == 200
    assert message['headers'] == []

    await input_queue.put({'type': 'invalid'})
    with pytest.raises(ValueError):
        await task


@pytest.mark.asyncio
async def test_jackie_to_asgi_unusual_scope():
    @jackie_to_asgi
    def app(request):
        pass

    with pytest.raises(ValueError):
        await app({'type': 'unusual'}, None, None)


@pytest.mark.asyncio
async def test_asgi_to_jackie_disconnect():
    @asgi_to_jackie
    async def view(scope, receive, send):
        assert scope['type'] == 'http'
        assert await receive() == {
            'type': 'http.request',
            'body': b'foo',
            'more_body': True,
        }
        assert await receive() == {
            'type': 'http.disconnect',
        }
        await send({
            'type': 'http.response.start',
            'status': 200,
        })
        await send({
            'type': 'http.response.body',
            'body': b'foo',
        })

    async def get_request_body():
        yield b'foo'
        raise Disconnect

    await view(Request(body=get_request_body()))


@pytest.mark.asyncio
async def test_asgi_to_jackie_no_more_messages():
    @asgi_to_jackie
    async def view(scope, receive, send):
        assert await receive() == {
            'type': 'http.request',
            'body': b'',
            'more_body': False,
        }
        with pytest.raises(ValueError):
            await receive()

    with pytest.raises(ValueError):
        await view(Request(body=[]))


@pytest.mark.asyncio
async def test_asgi_to_jackie_forward_exception():
    @asgi_to_jackie
    async def view(scope, receive, send):
        raise ValueError('test exception')

    with pytest.raises(ValueError) as exc_info:
        await view(Request(body=[]))

    assert str(exc_info.value) == 'test exception'


@pytest.mark.asyncio
async def test_asgi_to_jackie_unexpected_message():
    @asgi_to_jackie
    async def view(scope, receive, send):
        assert scope['type'] == 'http'
        await send({'type': 'invalid'})

    with pytest.raises(ValueError):
        await view(Request())

    @asgi_to_jackie
    async def view(scope, receive, send):
        assert scope['type'] == 'http'
        await send({'type': 'http.response.start', 'status': 200})
        await send({'type': 'invalid'})

    response = await view(Request())
    with pytest.raises(ValueError):
        await response.body()


@pytest.mark.asyncio
async def test_jackie_to_asgi_websocket():
    @jackie_to_asgi
    async def echo(socket):
        await socket.accept()
        while True:
            try:
                message = await socket.receive_bytes()
            except Disconnect:
                break
            try:
                await socket.send_text(message.decode())
            except ValueError:
                await socket.send_bytes(message)

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(
        echo(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({
        'type': 'websocket.connect',
    })
    assert await output_queue.get() == {
        'type': 'websocket.accept',
        'headers': [],
    }
    await input_queue.put({
        'type': 'websocket.receive',
        'text': 'foo',
    })
    assert await output_queue.get() == {
        'type': 'websocket.send',
        'bytes': None,
        'text': 'foo',
    }
    await input_queue.put({
        'type': 'websocket.receive',
        'bytes': 'bar',
    })
    assert await output_queue.get() == {
        'type': 'websocket.send',
        'bytes': None,
        'text': 'bar',
    }
    await input_queue.put({
        'type': 'websocket.disconnect',
    })
    await task


@pytest.mark.asyncio
async def test_jackie_to_asgi_websocket_message_types():
    @jackie_to_asgi
    async def echo(socket):
        await socket.accept()

        assert await socket.receive_text() == 'foo'
        assert await socket.receive_text() == 'bar'

        assert await socket.receive_bytes() == b'baz'
        assert await socket.receive_bytes() == b'qux'

        assert await socket.receive_json() == {'foo': 'bar'}

        await socket.send_text('foo')
        with pytest.raises(TypeError):
            await socket.send_text(b'bar')

        await socket.send_bytes(b'baz')
        with pytest.raises(TypeError):
            await socket.send_bytes('qux')

        await socket.send_json({'foo': 'bar'})

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(
        echo(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({
        'type': 'websocket.connect',
    })
    assert await output_queue.get() == {
        'type': 'websocket.accept',
        'headers': [],
    }
    await input_queue.put({'type': 'websocket.receive', 'text': 'foo'})
    await input_queue.put({'type': 'websocket.receive', 'bytes': b'bar'})
    await input_queue.put({'type': 'websocket.receive', 'bytes': b'baz'})
    await input_queue.put({'type': 'websocket.receive', 'text': 'qux'})
    await input_queue.put({
        'type': 'websocket.receive',
        'text': '{"foo": "bar"}',
    })
    assert await output_queue.get() == {
        'type': 'websocket.send',
        'text': 'foo',
        'bytes': None,
    }
    assert await output_queue.get() == {
        'type': 'websocket.send',
        'text': None,
        'bytes': b'baz',
    }
    assert await output_queue.get() == {
        'type': 'websocket.send',
        'text': '{"foo": "bar"}',
        'bytes': None,
    }
    await task


@pytest.mark.asyncio
async def test_jackie_to_asgi_websocket_double_accept():
    @jackie_to_asgi
    async def echo(socket):
        await socket.accept()
        with pytest.raises(ValueError):
            await socket.accept()

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }

    task = asyncio.ensure_future(
        echo(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    assert await output_queue.get() == {
        'type': 'websocket.accept',
        'headers': [],
    }
    await task


@pytest.mark.asyncio
async def test_jackie_to_asgi_websocket_double_close():
    @jackie_to_asgi
    async def echo(socket):
        await socket.close()
        with pytest.raises(ValueError):
            await socket.close()

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }

    task = asyncio.ensure_future(
        echo(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    assert await output_queue.get() == {
        'type': 'websocket.close',
        'code': 1000,
    }
    await task


@pytest.mark.asyncio
async def test_jackie_to_asgi_websocket_receive_before_accept():
    @jackie_to_asgi
    async def echo(socket):
        with pytest.raises(ValueError):
            await socket.receive_bytes()

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }

    task = asyncio.ensure_future(
        echo(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    await task


@pytest.mark.asyncio
async def test_jackie_to_asgi_websocket_send_before_accept():
    @jackie_to_asgi
    async def echo(socket):
        with pytest.raises(ValueError):
            await socket.send_bytes(b'foo')

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }

    task = asyncio.ensure_future(
        echo(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    await task


@pytest.mark.asyncio
async def test_jackie_to_asgi_websocket_unexpected_message():
    @jackie_to_asgi
    async def echo(socket):
        await socket.accept()
        with pytest.raises(ValueError):
            await socket.receive_bytes()

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }

    task = asyncio.ensure_future(
        echo(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    await input_queue.put({'type': 'unexpected'})
    await task


@pytest.mark.asyncio
async def test_jackie_to_asgi_send_invalid_type():
    @jackie_to_asgi
    async def echo(socket):
        await socket.accept()
        with pytest.raises(TypeError):
            await socket._send(123)

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }

    task = asyncio.ensure_future(
        echo(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    await task


@pytest.mark.asyncio
async def test_asgi_to_jackie_websocket():
    @asgi_to_jackie
    async def echo(scope, receive, send):
        assert scope['type'] == 'websocket'
        assert (await receive())['type'] == 'websocket.connect'
        await send({'type': 'websocket.accept'})
        while True:
            message = await receive()
            if message['type'] == 'websocket.close':
                break
            assert message['type'] == 'websocket.receive'
            await send({**message, 'type': 'websocket.send'})

    async def get_messages():
        yield 'foo'
        yield b'bar'
        raise Disconnect()

    connect_queue = asyncio.Queue()
    message_queue = asyncio.Queue()

    socket = Socket(
        accept=lambda *args, **kwargs: connect_queue.put(True),
        close=lambda *args, **kwargs: connect_queue.put(False),
        receive=get_messages().__anext__,
        send=message_queue.put,
    )

    task = asyncio.ensure_future(echo(socket))
    assert await connect_queue.get() is True
    assert await message_queue.get() == 'foo'
    assert await message_queue.get() == b'bar'
    await task

    async def get_wrong_messages():
        yield True

    connect_queue = asyncio.Queue()
    message_queue = asyncio.Queue()

    socket = Socket(
        accept=lambda *args, **kwargs: connect_queue.put(True),
        close=lambda *args, **kwargs: connect_queue.put(False),
        receive=get_wrong_messages().__anext__,
        send=message_queue.put,
    )

    task = asyncio.ensure_future(echo(socket))
    assert await connect_queue.get() is True
    with pytest.raises(ValueError):
        await task


@pytest.mark.asyncio
async def test_asgi_to_jackie_websocket_close():
    @asgi_to_jackie
    async def close_it(scope, receive, send):
        assert scope['type'] == 'websocket'
        assert (await receive())['type'] == 'websocket.connect'
        await send({'type': 'websocket.close'})

    async def get_messages():
        for value in []:
            yield value

    connect_queue = asyncio.Queue()
    message_queue = asyncio.Queue()

    socket = Socket(
        accept=lambda *args, **kwargs: connect_queue.put(True),
        close=lambda *args, **kwargs: connect_queue.put(False),
        receive=get_messages().__anext__,
        send=message_queue.put,
    )

    task = asyncio.ensure_future(close_it(socket))
    assert await connect_queue.get() is False
    await task


@pytest.mark.asyncio
async def test_asgi_to_jackie_websocket_send_validation():
    @asgi_to_jackie
    async def close_it(scope, receive, send):
        assert scope['type'] == 'websocket'
        assert (await receive())['type'] == 'websocket.connect'
        with pytest.raises(ValueError):
            await send({'type': 'websocket.send'})
        with pytest.raises(ValueError):
            await send({'type': 'unexpected'})

    async def get_messages():
        for value in []:
            yield value

    connect_queue = asyncio.Queue()
    message_queue = asyncio.Queue()

    socket = Socket(
        accept=lambda: connect_queue.put(True),
        close=lambda: connect_queue.put(False),
        receive=get_messages().__anext__,
        send=message_queue.put,
    )

    task = asyncio.ensure_future(close_it(socket))
    await task


@pytest.mark.asyncio
async def test_asgi_to_jackie_invalid_request():
    @asgi_to_jackie
    async def view(scope, receive, send):
        pass

    with pytest.raises(TypeError):
        await view(None)


@pytest.mark.asyncio
async def test_jackie_to_asgi_send_file():
    with tempfile.NamedTemporaryFile(suffix='.txt') as f:
        f.write(b'foobar')
        f.flush()

        @jackie_to_asgi
        async def app(request):
            offset = int(request.query.get('offset', '0'))
            size = int(request.query.get('size', '-1'))
            return Response(body=[SendFile(f.name, offset=offset, size=size)])

        input_queue = asyncio.Queue()
        output_queue = asyncio.Queue()

        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/',
            'query_string': b'',
            'headers': [],
            'extensions': {'http.response.zerocopysend': {}},
        }
        task = asyncio.ensure_future(
            app(scope, input_queue.get, output_queue.put)
        )

        message = await output_queue.get()
        assert message['type'] == 'http.response.start'
        assert message['status'] == 200
        assert message['headers'] == []

        chunks = []
        while True:
            message = await output_queue.get()
            if not (
                message['type'] == 'http.response.body' and
                message['body'] == b''
            ):
                chunks.append(message)
            if not message.pop('more_body'):
                break
        assert len(chunks) == 1
        assert set(chunks[0]) == {'type', 'file'}
        assert chunks[0]['type'] == 'http.response.zerocopysend'
        assert chunks[0]['file'].name == f.name
        await task

        input_queue = asyncio.Queue()
        output_queue = asyncio.Queue()

        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/',
            'query_string': b'offset=3',
            'headers': [],
            'extensions': {'http.response.zerocopysend': {}},
        }
        task = asyncio.ensure_future(
            app(scope, input_queue.get, output_queue.put)
        )

        message = await output_queue.get()
        assert message['type'] == 'http.response.start'
        assert message['status'] == 200
        assert message['headers'] == []

        chunks = []
        while True:
            message = await output_queue.get()
            if not (
                message['type'] == 'http.response.body' and
                message['body'] == b''
            ):
                chunks.append(message)
            if not message.pop('more_body'):
                break
        assert len(chunks) == 1
        assert set(chunks[0]) == {'type', 'file', 'offset'}
        assert chunks[0]['type'] == 'http.response.zerocopysend'
        assert chunks[0]['file'].name == f.name
        assert chunks[0]['offset'] == 3
        await task

        input_queue = asyncio.Queue()
        output_queue = asyncio.Queue()

        scope = {
            'type': 'http',
            'method': 'GET',
            'path': '/',
            'query_string': b'size=3',
            'headers': [],
            'extensions': {'http.response.zerocopysend': {}},
        }
        task = asyncio.ensure_future(
            app(scope, input_queue.get, output_queue.put)
        )

        message = await output_queue.get()
        assert message['type'] == 'http.response.start'
        assert message['status'] == 200
        assert message['headers'] == []

        chunks = []
        while True:
            message = await output_queue.get()
            if not (
                message['type'] == 'http.response.body' and
                message['body'] == b''
            ):
                chunks.append(message)
            if not message.pop('more_body'):
                break
        assert len(chunks) == 1
        assert set(chunks[0]) == {'type', 'file', 'count'}
        assert chunks[0]['type'] == 'http.response.zerocopysend'
        assert chunks[0]['file'].name == f.name
        assert chunks[0]['count'] == 3
        await task


@pytest.mark.asyncio
async def test_asgi_to_jackie_send_file():
    with tempfile.NamedTemporaryFile(suffix='.txt') as f:
        f.write(b'foobar')
        f.flush()

        @asgi_to_jackie
        async def view(scope, receive, send):
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [],
            })
            query = urllib.parse.parse_qs(scope['query_string'].decode())
            message = {
                'type': 'http.response.zerocopysend',
                'file': open(f.name, 'rb'),
            }
            if 'offset' in query:
                message['offset'] = int(query['offset'][-1])
            if 'size' in query:
                message['count'] = int(query['size'][-1])
            await send(message)

        response = await view(Request())
        assert await response.body() == b'foobar'

        response = await view(Request(query={'offset': 3}))
        assert await response.body() == b'bar'

        response = await view(Request(query={'size': 3}))
        assert await response.body() == b'foo'
