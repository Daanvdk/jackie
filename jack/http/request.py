from ..multidict import MultiDict, Headers
from .stream import Stream


class HttpRequest(Stream):

    def __init__(
        self, path='/', *, method='GET', query=[], headers=[], body=b'',
        **kwargs,
    ):
        super().__init__(body)
        self.path = path
        self.method = method
        self.query = MultiDict(query)
        self.headers = Headers(headers, **kwargs)
