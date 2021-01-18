import json

from ..multidict import Headers
from .stream import Stream


class HttpResponse(Stream):

    def __init__(self, body=b'', *, status=200, headers=[], **kwargs):
        super().__init__(body)
        self.status = status
        self.headers = Headers(headers, **kwargs)


class HttpResponseRedirect(HttpResponse):

    def __init__(self, to, *, status=304, **kwargs):
        super().__init__(status=status, **kwargs)
        self.headers['Location'] = to


class JsonResponse(HttpResponse):

    def __init__(self, body, **kwargs):
        super().__init__(json.dumps(body), **kwargs)
        self.headers.setdefault('Content-Type', 'application/json')
