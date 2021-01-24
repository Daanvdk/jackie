import json

from ..multidict import Headers
from .. import multipart
from .stream import Stream


# Base class

class Response(Stream):

    def __init__(self, body=b'', *, status=200, headers=[], **kwargs):
        super().__init__(body)
        self.status = status
        self.headers = Headers(headers, **kwargs)

    def _get_content_type(self):
        return self.headers.get('Content-Type')


# Subclasses

class FormResponse(Response):

    def __init__(self, body={}, boundary=None, **kwargs):
        if boundary is None:
            boundary = multipart.generate_boundary()
        body = multipart.serialize(body, boundary)
        super().__init__(body, **kwargs)
        self.headers.setdefault('Content-Type', (
            f'multipart/form-data; boundary={boundary}'
        ))


class HtmlResponse(Response):

    def __init__(self, body='', **kwargs):
        super().__init__(body.encode(), **kwargs)
        self.headers.setdefault('Content-Type', 'text/html; charset=UTF-8')


class JsonResponse(Response):

    def __init__(self, body={}, **kwargs):
        super().__init__(json.dumps(body).encode(), **kwargs)
        self.headers.setdefault('Content-Type', (
            'application/json; charset=UTF-8'
        ))


class RedirectResponse(Response):

    def __init__(self, location, *, status=304, **kwargs):
        super().__init__(status=status, **kwargs)
        self.headers['Location'] = location


class TextResponse(Response):

    def __init__(self, body='', **kwargs):
        super().__init__(body.encode(), **kwargs)
        self.headers.setdefault('Content-Type', 'text/plain; charset=UTF-8')
