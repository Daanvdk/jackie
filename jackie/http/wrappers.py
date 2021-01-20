import asyncio
import urllib.parse

from asgiref.compatibility import guarantee_single_callable

from .exceptions import Disconnect
from .request import Request
from .response import Response


# Jackie to ASGI

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


class JackieToAsgi:

    def __init__(self, view):
        self.view = view

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            request = Request(
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


# ASGI to Jackie

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


async def get_response_body(receive, cleanup):
    while True:
        message = await receive()
        if message['type'] == 'http.response.body':
            yield message.get('body', b'')
            if not message.get('more_body', False):
                break
        else:
            raise ValueError(f'unexpected message type: {message["type"]}')
    for task in cleanup:
        task.cancel()


class AsgiToJackie:

    def __init__(self, app):
        self.app = guarantee_single_callable(app)

    async def __call__(self, request, **params):
        input_queue = asyncio.Queue()
        output_queue = asyncio.Queue()

        body_task = asyncio.ensure_future(
            send_request_body(request.chunks(), input_queue.put)
        )

        async def receive():
            message_task = asyncio.ensure_future(input_queue.get())
            await asyncio.wait(
                [body_task, message_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            try:
                return message_task.result()
            except asyncio.InvalidStateError:
                message_task.cancel()
                raise ValueError('no more messages') from None

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
        app_task = asyncio.ensure_future(
            self.app(scope, receive, output_queue.put)
        )

        async def receive():
            message_task = asyncio.ensure_future(output_queue.get())
            await asyncio.wait(
                [app_task, message_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            try:
                return message_task.result()
            except asyncio.InvalidStateError:
                message_task.cancel()
                app_exception = app_task.exception()
                if app_exception:
                    raise app_exception from None
                else:
                    raise ValueError('expected more messages') from None

        message = await receive()
        if message['type'] != 'http.response.start':
            raise ValueError(f'unexpected message type: {message["type"]}')
        return Response(
            status=message['status'],
            headers=message.get('headers', []),
            body=get_response_body(receive, [body_task, app_task]),
        )


# Decorators

def jackie_to_asgi(view):
    if isinstance(view, AsgiToJackie):
        return view.app
    else:
        return JackieToAsgi(view)


def asgi_to_jackie(app):
    if isinstance(app, JackieToAsgi):
        return app.view
    else:
        return AsgiToJackie(app)