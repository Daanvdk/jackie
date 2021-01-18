import asyncio
import urllib.parse

import pytest

from jack.http import asgi_to_jack, jack_to_asgi, Request, TextResponse


# The same app implemented in Jack and ASGI

async def hello_world_view(request):
    name = request.query.get('name', 'World')
    return TextResponse(f'Hello, {name}!')


async def hello_world_app(scope, receive, send):
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


# Tests

@pytest.mark.asyncio
async def test_jack_to_asgi():
    app = jack_to_asgi(hello_world_view)

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'querystring': '',
        'headers': [],
    }
    task = asyncio.create_task(app(scope, input_queue.get, output_queue.put))

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
    task = asyncio.create_task(app(scope, input_queue.get, output_queue.put))

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
async def test_asgi_to_jack():
    view = asgi_to_jack(hello_world_app)

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
