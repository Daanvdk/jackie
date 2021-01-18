import asyncio
import urllib.parse

from asgiref.compatibility import guarantee_single_callable

from .exceptions import Disconnect
from .request import HttpRequest
from .response import HttpResponse


# Jack to ASGI

async def get_request_body(receive):
    while True:
        message = await receive()
        if message['type'] == 'http.request':
            yield message.get('body', b'')
            if not message.get('more_body', False):
                break
        elif message['type'] == 'http.disconnect':
            raise Disconnect
        else:
            raise ValueError(f'unexpected message type: {message["type"]}')


class JackToAsgi:

    def __init__(self, view):
        self.view = view

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            request = HttpRequest(
                method=scope['method'],
                path=scope['path'],
                query=urllib.parse.parse_qsl(scope['querystring']),
                headers=scope['headers'],
                body=get_request_body(receive),
            )
            try:
                response = await self.view(request, **scope.get('params', {}))
                await send({
                    'type': 'http.response.start',
                    'status': response.status,
                    'headers': [
                        (key.encode(), value.encode())
                        for key, value in response.headers.allitems()
                    ],
                })
                async for chunk in response.chunks():
                    await send({
                        'type': 'http.response.body',
                        'body': chunk,
                        'more_body': True,
                    })
                await send({
                    'type': 'http.response.body',
                    'body': b'',
                    'more_body': False,
                })
            except Disconnect:
                pass

        elif scope['type'] == 'websocket':
            raise NotImplementedError

        else:
            raise ValueError(f'unsupported scope type: {scope["type"]}')


# ASGI to Jack

async def send_request_body(chunks, send):
    try:
        async for chunk in chunks:
            await send({
                'type': 'http.request',
                'body': chunk,
                'more_body': True,
            })
        await send({
            'type': 'http.request',
            'body': b'',
            'more_body': False,
        })
    except Disconnect:
        await send({'type': 'http.disconnect'})


async def get_response_body(receive):
    while True:
        message = await receive()
        if message['type'] == 'http.response.body':
            yield message.get('body', b'')
            if not message.get('more_body', False):
                break
        else:
            raise ValueError(f'unexpected message type: {message["type"]}')


class AsgiToJack:

    def __init__(self, app):
        self.app = guarantee_single_callable(app)

    async def __call__(self, request, **params):
        input_queue = asyncio.Queue()
        output_queue = asyncio.Queue()
        scope = {
            'type': 'http',
            'method': request.method,
            'path': request.path,
            'querystring': urllib.parse.urlencode(
                list(request.query.allitems())
            ),
            'headers': [
                (key.encode(), value.encode())
                for key, value in request.headers.allitems()
            ],
            'params': params,
        }
        asyncio.create_task(
            self.app(scope, input_queue.get, output_queue.put)
        )
        asyncio.create_task(
            send_request_body(request.chunks(), input_queue.put)
        )
        message = await output_queue.get()
        if message['type'] != 'http.response.start':
            raise ValueError(f'unexpected message type: {message["type"]}')
        return HttpResponse(
            status=message['status'],
            headers=message.get('headers', []),
            body=get_response_body(output_queue.get),
        )


# Decorators

def jack_to_asgi(view):
    if isinstance(view, AsgiToJack):
        return view.app
    else:
        return JackToAsgi(view)


def asgi_to_jack(app):
    if isinstance(app, JackToAsgi):
        return app.view
    else:
        return AsgiToJack(app)
