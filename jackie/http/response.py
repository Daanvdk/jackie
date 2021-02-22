import json

from ..multidict import Headers
from .. import multipart
from .stream import Stream


def form_body(body):
    boundary = multipart.generate_boundary()
    body = multipart.serialize(body, boundary)
    headers = {'Content-Type': f'multipart/form-data; boundary={boundary}'}
    return 200, body, headers


def json_body(body):
    body = json.dumps(body).encode()
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    return 200, body, headers


def text_body(body):
    body = body.encode()
    headers = {'Content-Type': 'text/plain; charset=UTF-8'}
    return 200, body, headers


def html_body(body):
    body = body.encode()
    headers = {'Content-Type': 'text/html; charset=UTF-8'}
    return 200, body, headers


def redirect_body(body):
    headers = {'Location': body}
    body = b''
    return 304, body, headers


def base_body(body):
    return 200, body, {}


BODY_TYPES = {
    'form': form_body,
    'json': json_body,
    'text': text_body,
    'html': html_body,
    'redirect': redirect_body,
    'body': base_body,
}


class Response(Stream):

    def __init__(
        self, *, status=None, content_type=None, headers=[], set_cookies=[],
        **kwargs,
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
        default_status, body, default_headers = body or (200, b'', {})

        super().__init__(body)
        self.status = default_status if status is None else status
        self.headers = Headers(headers, **kwargs)
        if content_type is not None:
            self.headers.setdefault('Content-Type', content_type)
        for key, value in default_headers.items():
            self.headers.setdefault(key, value)

        for cookie in set_cookies:
            self.headers.appendlist('Set-Cookie', cookie.serialize())

    def _get_content_type(self):
        return self.headers.get('Content-Type')

    @property
    def ok(self):
        return self.status < 400
