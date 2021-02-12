import json

from ..multidict import Headers
from .. import multipart
from .stream import Stream


# Base class

class Response(Stream):

    def __init__(
        self, body=b'', *, status=200, content_type=None, headers=[], **kwargs,
    ):
        super().__init__(body)
        self.status = status

        if content_type is not None:
            if content_type.startswith('multipart/'):
                boundary = kwargs.pop('boundary')
                content_type += f'; boundary={boundary}'
            elif 'charset' in kwargs:
                charset = kwargs.pop('charset')
                content_type += f'; charset={charset}'

        self.headers = Headers(headers, **kwargs)

        if content_type is not None:
            self.headers.setdefault('Content-Type', content_type)

    def _get_content_type(self):
        return self.headers.get('Content-Type')

    @property
    def ok(self):
        return self.status < 400


# Subclasses

class FormResponse(Response):

    def __init__(self, body={}, boundary=None, **kwargs):
        if boundary is None:
            boundary = multipart.generate_boundary()
        body = multipart.serialize(body, boundary)
        super().__init__(
            body,
            content_type='multipart/form-data',
            boundary=boundary,
            **kwargs
        )


class HtmlResponse(Response):

    def __init__(self, body='', **kwargs):
        super().__init__(
            body.encode(),
            content_type='text/html',
            charset='UTF-8',
            **kwargs,
        )


class JsonResponse(Response):

    def __init__(self, body={}, **kwargs):
        super().__init__(
            json.dumps(body).encode(),
            content_type='application/json',
            charset='UTF-8',
            **kwargs,
        )


class RedirectResponse(Response):

    def __init__(self, location, *, status=304, **kwargs):
        super().__init__(status=status, **kwargs)
        self.headers['Location'] = location


class TextResponse(Response):

    def __init__(self, body='', **kwargs):
        super().__init__(
            body.encode(),
            content_type='text/plain',
            charset='UTF-8',
            **kwargs,
        )
        self.headers.setdefault('Content-Type', 'text/plain; charset=UTF-8')
