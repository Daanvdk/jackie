import json

from ..multidict import MultiDict, Headers
from .. import multipart
from ..parse import parse_cookies
from .stream import Stream


def form_body(body):
    boundary = multipart.generate_boundary()
    body = multipart.serialize(body, boundary)
    return body, f'multipart/form-data; boundary={boundary}'


def json_body(body):
    body = json.dumps(body).encode()
    return body, 'application/json; charset=UTF-8'


def text_body(body):
    body = body.encode()
    return body, 'text/plain; charset=UTF-8'


def base_body(body):
    return body, None


BODY_TYPES = {
    'form': form_body,
    'json': json_body,
    'text': text_body,
    'body': base_body,
}


class Request(Stream):

    def __init__(
        self, path='/', *, method='GET', query=[], headers=[], **kwargs,
    ):
        body = None
        for key, get_body in BODY_TYPES.items():
            try:
                data = kwargs.pop(key)
            except KeyError:
                continue
            if body is None:
                body = get_body(data)
            else:
                raise ValueError('multiple body types supplied')
        body, content_type = body or (b'', None)

        super().__init__(body)
        self.path = path
        self.method = method
        self.query = MultiDict(query)
        self.headers = Headers(headers, **kwargs)
        if content_type is not None:
            self.headers.setdefault('Content-Type', content_type)

        self.router = None
        self.view_name = None

    def _get_content_type(self):
        return self.headers.get('Content-Type')

    @property
    def cookies(self):
        return parse_cookies(self.headers.get('Cookie', ''))
