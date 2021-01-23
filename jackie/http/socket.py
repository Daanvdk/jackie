import json

from ..multidict import MultiDict, Headers


class Socket:

    method = 'WEBSOCKET'

    def __init__(
        self, path='/', *, accept, close, receive, send, query=[], headers=[],
        **kwargs
    ):
        self.path = path
        self.query = MultiDict(query)
        self.headers = Headers(headers, **kwargs)

        self.accept = accept
        self.close = close
        self._receive = receive
        self._send = send

        self.router = None
        self.view_name = None

    async def receive_bytes(self):
        message = await self._receive()
        if isinstance(message, str):
            message = message.encode()
        return message

    async def receive_text(self):
        message = await self._receive()
        if isinstance(message, bytes):
            message = message.decode()
        return message

    async def receive_json(self):
        return json.loads(await self.receive_text())

    async def send_bytes(self, message):
        if not isinstance(message, bytes):
            raise TypeError(
                f'message must be bytes, not {message.__class__.__name__}'
            )
        return await self._send(message)

    async def send_text(self, message):
        if not isinstance(message, str):
            raise TypeError(
                f'message must be str, not {message.__class__.__name__}'
            )
        return await self._send(message)

    async def send_json(self, message):
        return await self.send_text(json.dumps(message))
