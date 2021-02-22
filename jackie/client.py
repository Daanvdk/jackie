import asyncio
from datetime import datetime, timezone, timedelta

from .http import asgi_to_jackie, Cookie, Request, Socket
from .http.exceptions import Disconnect
from .multidict import Headers
from .bridge import bridge
from .parse import parse_set_cookie
from .serialize import serialize_cookies


class Client:

    def __init__(self, app):
        self._view = asgi_to_jackie(app)
        self.cookies = {}

    def _get_cookies(self, path):
        cookies = {}
        now = datetime.now().astimezone(timezone.utc)
        for name, cookie in list(self.cookies.items()):
            if cookie.expires is not None and cookie.expires <= now:
                self.cookies.pop(name)
                continue
            if cookie.path is not None and not path.startswith(cookie.path):
                continue
            cookies[cookie.name] = cookie.value
        return serialize_cookies(cookies)

    def _set_cookies(self, headers):
        now = datetime.now().astimezone(timezone.utc)
        for cookie in headers.getlist('Set-Cookie'):
            name, value, params = parse_set_cookie(cookie)
            try:
                params['expires'] = (
                    now + timedelta(seconds=params.pop('max_age'))
                )
            except KeyError:
                pass
            if 'expires' in params and params['expires'] <= now:
                self.cookies.pop(name, None)
                continue
            else:
                print('STILL VALID')
            params.setdefault('same_site', 'lax')
            self.cookies[name] = Cookie(name, value, **params)

    async def request(self, *args, **kwargs):
        request = Request(*args, **kwargs)
        request.headers.setdefault('Cookie', self._get_cookies(request.path))
        response = await self._view(request)
        self._set_cookies(response.headers)
        return response

    async def get(self, *args, **kwargs):
        return await self.request(*args, method='GET', **kwargs)

    async def head(self, *args, **kwargs):
        return await self.request(*args, method='HEAD', **kwargs)

    async def post(self, *args, **kwargs):
        return await self.request(*args, method='POST', **kwargs)

    async def put(self, *args, **kwargs):
        return await self.request(*args, method='PUT', **kwargs)

    async def delete(self, *args, **kwargs):
        return await self.request(*args, method='DELETE', **kwargs)

    async def connect(self, *args, **kwargs):
        return await self.request(*args, method='CONNECT', **kwargs)

    async def options(self, *args, **kwargs):
        return await self.request(*args, method='OPTIONS', **kwargs)

    async def trace(self, *args, **kwargs):
        return await self.request(*args, method='TRACE', **kwargs)

    async def patch(self, *args, **kwargs):
        return await self.request(*args, method='PATCH', **kwargs)

    async def websocket(self, *args, query=[], headers=[], **kwargs):
        put_in, get_in = bridge()
        put_out, get_out = bridge()

        view_state = 'handshake'

        async def view_to_res(message):
            try:
                await put_out(message)
            except (RuntimeError, GeneratorExit):
                raise Disconnect()

        async def view_from_res():
            return await get_in()

        async def view_accept(headers):
            nonlocal view_state
            if view_state != 'handshake':
                raise ValueError(
                    'can only accept connection during handshake'
                )
            view_state = 'open'
            self._set_cookies(headers)
            await view_to_res(('accept', headers))

        async def view_close(code):
            nonlocal view_state
            if view_state == 'closed':
                raise ValueError('connection already closed')
            view_state = 'closed'
            await view_to_res(('close', code))

        async def view_receive():
            nonlocal view_state
            if view_state != 'open':
                raise ValueError('connection is not open')
            message = await view_from_res()
            if message[0] == 'close':
                view_state = 'closed'
                raise Disconnect(message[1])
            assert message[0] == 'message'
            return message[1]

        async def view_send(message):
            nonlocal view_state
            if view_state != 'open':
                raise ValueError('connection is not open')
            await view_to_res(('message', message))

        async def view_coro():
            try:
                socket = Socket(
                    *args,
                    accept=view_accept,
                    close=view_close,
                    receive=view_receive,
                    send=view_send,
                    query=query,
                    headers=Headers(headers, **kwargs),
                )
                socket.headers.setdefault('Cookie', (
                    self._get_cookies(socket.path)
                ))
                await self._view(socket)
            except Disconnect:
                pass

        view_task = asyncio.ensure_future(view_coro())

        async def res_to_view(message):
            put_task = asyncio.ensure_future(put_in(message))
            await asyncio.wait(
                [view_task, put_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            try:
                put_task.result()
            except asyncio.InvalidStateError:
                put_task.cancel()
                exception = view_task.exception()
                if exception is not None:
                    raise exception
                else:
                    raise ValueError('view returned early')

        async def res_from_view():
            get_task = asyncio.ensure_future(get_out())
            await asyncio.wait(
                [view_task, get_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            try:
                message = get_task.result()
                return message
            except asyncio.InvalidStateError:
                get_task.cancel()
                exception = view_task.exception()
                if exception is not None:
                    raise exception
                else:
                    raise ValueError('view returned early')

        res_state = 'handshake'

        async def res_accept(headers):
            raise ValueError('cannot call accept on reverse socket')

        async def res_close(code):
            nonlocal res_state
            if res_state == 'closed':
                raise ValueError('connection already closed')
            res_state = 'closed'
            await res_to_view(('close', code))

        async def res_receive():
            nonlocal res_state
            if res_state != 'open':
                raise ValueError('connection is not open')
            message = await res_from_view()
            if message[0] == 'close':
                res_state = 'closed'
                raise Disconnect(message[1])
            assert message[0] == 'message'
            return message[1]

        async def res_send(message):
            nonlocal res_state
            if res_state != 'open':
                raise ValueError('connection is not open')
            await res_to_view(('message', message))

        async def res_accepted():
            nonlocal res_state
            if res_state != 'handshake':
                raise ValueError('connection is not in handshake')
            message = await res_from_view()
            if message[0] == 'close':
                res_state = 'closed'
                raise Disconnect(message[1])
            res_state = 'open'
            assert message[0] == 'accept'
            return message[1]

        async def res_closed():
            nonlocal res_state
            if res_state == 'closed':
                raise ValueError('connection already closed')
            message = await res_from_view()
            if res_state == 'handshake' and message[0] == 'accept':
                res_state = 'open'
            assert message[0] == 'close', (
                f'expected close, got {message[0]} instead'
            )
            res_state = 'closed'
            return message[1]

        res = Socket(
            accept=res_accept,
            close=res_close,
            receive=res_receive,
            send=res_send,
        )
        res.accepted = res_accepted
        res.closed = res_closed
        return res
