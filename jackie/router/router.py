from ..http import TextResponse
from ..http.wrappers import (
    asgi_to_jackie, jackie_to_asgi, AsgiToJackie, JackieToAsgi,
)
from .matcher import Matcher


async def not_found(request):
    return TextResponse('Not Found', status=404)


async def method_not_allowed(request, methods):
    return TextResponse(
        'Method Not Allowed',
        status=405,
        allow=', '.join(sorted(methods)),
    )


@asgi_to_jackie
async def websocket_not_found(scope, receive, send):
    message = await receive()
    if message['type'] != 'websocket.connect':
        raise ValueError(f'unexpected message: {message["type"]}')
    await send({'type': 'websocket.close'})


class ResolvedView(AsgiToJackie):

    def __init__(self, view, params):
        super().__init__(ResolvedApp(self))
        self.view = view
        self.params = params

    async def __call__(self, request, **params):
        params.update(self.params)
        return await self.view(request, **params)


class ResolvedApp(JackieToAsgi):

    async def __call__(self, scope, receive, send):
        params = {**scope.get('params', {}), **self.view.params}
        scope = {**scope, 'params': params}
        app = jackie_to_asgi(self.view.view)
        return await app(scope, receive, send)


class Router(JackieToAsgi):

    def __init__(self):
        super().__init__(JackieRouter(self))
        self._routes = []
        self._not_found = not_found
        self._method_not_allowed = method_not_allowed
        self._websocket_not_found = websocket_not_found

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

    def _get_view(self, method, path):
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
            if method == 'WEBSOCKET':
                view = self._websocket_not_found
                params = {}
            elif allowed_methods:
                view = self._method_not_allowed
                params = {'methods': allowed_methods}
            else:
                view = self._not_found
                params = {}

        return ResolvedView(view, params)

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http':
            method = scope['method']
        elif scope['type'] == 'websocket':
            method = 'WEBSOCKET'
        else:
            raise ValueError(f'unsupported scope type: {scope["type"]}')
        app = jackie_to_asgi(self._get_view(method, scope['path']))
        return await app(scope, receive, send)


class JackieRouter(AsgiToJackie):

    async def __call__(self, request, **params):
        view = self.app._get_view(request.method, request.path)
        return await view(request, **params)
