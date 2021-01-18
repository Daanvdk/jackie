import json

from ..multidict import MultiDict, Headers
from .stream import Stream


# Base class

class Request(Stream):

    def __init__(
        self, path='/', *, method='GET', query=[], headers=[], body=b'',
        **kwargs,
    ):
        super().__init__(body)
        self.path = path
        self.method = method
        self.query = MultiDict(query)
        self.headers = Headers(headers, **kwargs)


# Subclasses

class JsonRequest(Request):

    def __init__(self, path='/', body={}, **kwargs):
        super().__init__(path=path, body=json.dumps(body).encode(), **kwargs)
        self.headers.setdefault('Content-Type', (
            'application/json; charset=UTF-8'
        ))


class TextRequest(Request):

    def __init__(self, path='/', body='', **kwargs):
        super().__init__(path=path, body=body.encode(), **kwargs)
        self.headers.setdefault('Content-Type', 'text/plain; charset=UTF-8')
