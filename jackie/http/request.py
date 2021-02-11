import json

from ..multidict import MultiDict, Headers
from .. import multipart
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

        self.router = None
        self.view_name = None

    def _get_content_type(self):
        return self.headers.get('Content-Type')


# Subclasses

class FormRequest(Request):

    def __init__(self, path='/', body={}, boundary=None, **kwargs):
        if boundary is None:
            boundary = multipart.generate_boundary()
        body = multipart.serialize(body, boundary)
        super().__init__(path=path, body=body, **kwargs)
        self.headers.setdefault('Content-Type', (
            f'multipart/form-data; boundary={boundary}'
        ))


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
