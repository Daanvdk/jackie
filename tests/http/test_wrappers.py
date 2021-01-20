import asyncio
import urllib.parse

import pytest

from jackie.http import (
    asgi_to_jackie, jackie_to_asgi, Request, TextResponse, Response,
)
from jackie.http.exceptions import Disconnect


@pytest.mark.asyncio
async def test_jackie_to_asgi():
    @jackie_to_asgi
    async def app(request):
        name = request.query.get('name', 'World')
        return TextResponse(f'Hello, {name}!')

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'querystring': '',
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
        'querystring': 'name=Jack',
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
        query = urllib.parse.parse_qs(scope['querystring'])
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
        return Response(request.chunks())

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'querystring': 'name=Jack',
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
