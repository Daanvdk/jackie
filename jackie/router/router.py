from ..http import TextResponse
from ..http.wrappers import jackie_to_asgi, AsgiToJackie, JackieToAsgi
from .matcher import Matcher


async def not_found(request):
    return TextResponse('Not Found', status=404)


async def method_not_allowed(request, methods):
    return TextResponse(
        'Method Not Allowed',
        status=405,
        allow=', '.join(sorted(methods)),
    )


class Router(JackieToAsgi):

    def __init__(self):
        super().__init__(JackieRouter(self))
        self._routes = []
        self._not_found = not_found
        self._method_not_allowed = method_not_allowed

    # Configuration

    def route(self, methods, matcher, view=None):
        if view is None:
            def decorator(view):
                self.route(methods, matcher, view)
                return view
            return decorator
        if isinstance(methods, str):
            methods = {methods}
        if not isinstance(matcher, Matcher):
            matcher = Matcher(matcher)
        self._routes.append((methods, matcher, view))
        return self

    def include(self, matcher, router):
        if not isinstance(matcher, Matcher):
            matcher = Matcher(matcher)
        self._routes.append((None, matcher, router))
        return self

    def not_found(self, view):
        self._not_found = view
        return self

    def method_not_allowed(self, view):
        self._method_not_allowed = view
        return self

    # Method shorthands

    def get(self, *args, **kwargs):
        return self.route('GET', *args, **kwargs)

    def head(self, *args, **kwargs):
        return self.route('HEAD', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.route('POST', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.route('PUT', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.route('DELETE', *args, **kwargs)

    def connect(self, *args, **kwargs):
        return self.route('CONNECT', *args, **kwargs)

    def options(self, *args, **kwargs):
        return self.route('OPTIONS', *args, **kwargs)

    def trace(self, *args, **kwargs):
        return self.route('TRACE', *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.route('PATCH', *args, **kwargs)

    def websocket(self, *args, **kwargs):
        return self.route('WEBSOCKET', *args, **kwargs)

    # Application

    def _flat_routes(self, *, prefix=None):
        for methods, matcher, view in self._routes:
            if prefix is not None:
                matcher = prefix + matcher
            if methods is None:
                yield from view._flat_routes(prefix=matcher)
            else:
                yield methods, matcher, view

    def _resolve(self, method, path):
        allowed_methods = set()

        for methods, matcher, view in self._flat_routes():
            try:
                params = matcher.match(path)
            except Matcher.Error:
                continue
            allowed_methods.update(methods)
            if method in allowed_methods:
                break
        else:
            if allowed_methods:
                view = self._method_not_allowed
                params = {'methods': allowed_methods}
            else:
                view = self._not_found
                params = {}

        return view, params

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            method = scope['method']
        elif scope['type'] == 'websocket':
            method = 'WEBSOCKET'
        else:
            raise ValueError(f'unsupported scope type: {scope["type"]}')
        view, params = self._resolve(method, scope['path'])
        try:
            params = {**scope['params'], **params}
        except KeyError:
            pass
        scope = {**scope, 'params': params}
        app = jackie_to_asgi(view)
        return await app(scope, receive, send)


class JackieRouter(AsgiToJackie):

    def __init__(self, app):
        super().__init__(app)

    async def __call__(self, request, **params):
        view, subparams = self.app._resolve(request.method, request.path)
        params = {**params, **subparams}
        return await view(request, **params)
