import asyncio
import urllib.parse

from asgiref.compatibility import guarantee_single_callable

from ..bridge import bridge
from ..multidict import Headers

from .exceptions import Disconnect
from .request import Request
from .response import Response
from .socket import Socket


# Jackie to ASGI

async def get_request_body(receive):
    while True:
        message = await receive()
        if message['type'] == 'http.request':
            yield message.get('body', b'')
            if not message.get('more_body', False):
                break
        elif message['type'] == 'http.disconnect':
            raise Disconnect()
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
                query=urllib.parse.parse_qsl(scope['query_string'].decode()),
                headers=scope['headers'],
                body=get_request_body(receive),
            )

            try:
                router_info = scope['jackie.router']
            except KeyError:
                params = {}
            else:
                request.router = router_info['router']
                request.view_name = router_info['name']
                params = router_info['params']

            try:
                response = await self.view(request, **params)
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
            message = await receive()
            if message['type'] != 'websocket.connect':
                raise ValueError(f'unexpected message: {message["type"]}')

            state = 'handshake'

            async def accept(headers=[], **kwargs):
                nonlocal state
                if state != 'handshake':
                    raise ValueError(
                        'can only accept connection during handshake'
                    )
                state = 'open'
                headers = Headers(headers, **kwargs)
                await send({
                    'type': 'websocket.accept',
                    'headers': [
                        (key.encode(), value.encode())
                        for key, value in headers.allitems()
                    ],
                })

            async def close(code=1000):
                nonlocal state
                if state == 'closed':
                    raise ValueError('connection already closed')
                state = 'closed'
                await send({'type': 'websocket.close', 'code': code})

            async def receive_message():
                nonlocal state
                if state != 'open':
                    raise ValueError('connection is not open')
                message = await receive()
                if message['type'] == 'websocket.receive':
                    return message.get('text') or message.get('bytes')
                elif message['type'] == 'websocket.disconnect':
                    state = 'closed'
                    raise Disconnect(message.get('code', 1000))
                else:
                    raise ValueError(f'unexpected type: {message["type"]}')

            async def send_message(message):
                nonlocal state
                if state != 'open':
                    raise ValueError('connection is not open')
                if isinstance(message, str):
                    message = {
                        'type': 'websocket.send',
                        'text': message,
                        'bytes': None,
                    }
                elif isinstance(message, bytes):
                    message = {
                        'type': 'websocket.send',
                        'text': None,
                        'bytes': message,
                    }
                else:
                    raise TypeError(
                        'message must be either str or bytes, not '
                        f'{message.__class__.__name__}'
                    )
                await send(message)

            socket = Socket(
                path=scope['path'],
                query=urllib.parse.parse_qsl(scope['query_string'].decode()),
                headers=scope['headers'],
                accept=accept,
                close=close,
                receive=receive_message,
                send=send_message,
            )

            try:
                router_info = scope['jackie.router']
            except KeyError:
                params = {}
            else:
                socket.router = router_info['router']
                socket.view_name = router_info['name']
                params = router_info['params']

            return await self.view(socket, **params)

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
    except (RuntimeError, GeneratorExit):
        pass


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
        if isinstance(request, Request):
            put_in, get_in = bridge()
            put_out, get_out = bridge()

            async def receive():
                message_task = asyncio.ensure_future(get_in())
                await asyncio.wait(
                    [body_task, message_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                try:
                    return message_task.result()
                except asyncio.InvalidStateError:
                    message_task.cancel()
                    raise ValueError('no more messages') from None

            async def send(message):
                try:
                    await put_out(message)
                except (RuntimeError, GeneratorExit):
                    pass

            body_task = asyncio.ensure_future(
                send_request_body(request.chunks(), put_in)
            )

            scope = {
                'type': 'http',
                'method': request.method,
                'path': request.path,
                'query_string': urllib.parse.urlencode(
                    list(request.query.allitems())
                ).encode(),
                'headers': [
                    (key.encode(), value.encode())
                    for key, value in request.headers.allitems()
                ],
                'jackie.router': {
                    'router': request.router,
                    'name': request.view_name,
                    'params': params,
                },
            }
            app_task = asyncio.ensure_future(
                self.app(scope, receive, send)
            )

            async def receive():
                message_task = asyncio.ensure_future(get_out())
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
                        raise app_exception
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

        elif isinstance(request, Socket):
            scope = {
                'type': 'websocket',
                'path': request.path,
                'query_string': urllib.parse.urlencode(
                    list(request.query.allitems())
                ).encode(),
                'headers': [
                    (key.encode(), value.encode())
                    for key, value in request.headers.allitems()
                ],
                'jackie.router': {
                    'router': request.router,
                    'name': request.view_name,
                    'params': params,
                },
            }

            first = True

            async def receive():
                nonlocal first
                if first:
                    first = False
                    return {'type': 'websocket.connect'}
                try:
                    message = await request._receive()
                except Disconnect as e:
                    return {'type': 'websocket.close', 'code': e.code}
                if isinstance(message, str):
                    return {
                        'type': 'websocket.receive',
                        'bytes': None,
                        'text': message,
                    }
                elif isinstance(message, bytes):
                    return {
                        'type': 'websocket.receive',
                        'bytes': message,
                        'text': None,
                    }
                else:
                    raise ValueError(
                        'message must be either str or bytes, not '
                        f'{message.__class__.__name__}'
                    )

            async def send(message):
                if message['type'] == 'websocket.accept':
                    await request.accept(headers=message.get('headers', []))
                elif message['type'] == 'websocket.close':
                    await request.close(code=message.get('code', 1000))
                elif message['type'] == 'websocket.send':
                    if message.get('text'):
                        await request.send_text(message['text'])
                    elif message.get('bytes'):
                        await request.send_bytes(message['bytes'])
                    else:
                        raise ValueError('send without content')
                else:
                    raise ValueError(
                        f'unexpected message type: {message["type"]}'
                    )

            return await self.app(scope, receive, send)

        else:
            raise TypeError(
                'request must be Request or Socket, not '
                f'{request.__class__.__name__}'
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
