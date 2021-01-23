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


async def websocket_not_found(socket):
    await socket.close()


class ResolvedView(AsgiToJackie):

    def __init__(self, view, params):
        super().__init__(ResolvedApp(self))
        if isinstance(view, ResolvedView):
            params = {**params, **view.params}
            view = view.view
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


class NoView(Exception):

    def __init__(self, allowed_methods):
        self.allowed_methods = allowed_methods


class Router(JackieToAsgi):

    def __init__(self):
        super().__init__(JackieRouter(self))
        self._routes = []
        self._not_found = None
        self._method_not_allowed = None
        self._websocket_not_found = None
        self._middlewares = []

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
        return view

    def method_not_allowed(self, view):
        self._method_not_allowed = view
        return view

    def middleware(self, middleware):
        self._middlewares.append(middleware)
        return middleware

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

    def _get_view(self, method, path, *, root=True, base_params={}):
        allowed_methods = set()

        for methods, matcher, view in self._routes:
            if methods is None:
                try:
                    params, path = matcher.match(path)
                except Matcher.Error:
                    continue
                try:
                    view = view._get_view(
                        method, path,
                        root=False, base_params={**base_params, **params},
                    )
                except NoView as no_view:
                    methods = no_view.allowed_methods
                else:
                    break
            else:
                try:
                    params = matcher.fullmatch(path)
                except Matcher.Error:
                    continue
                if method in methods:
                    break
            allowed_methods.update(methods)
        else:
            if method == 'WEBSOCKET':
                view = self._websocket_not_found
                params = {**base_params}
                if view is None and root:
                    view = websocket_not_found
            elif allowed_methods:
                view = self._method_not_allowed
                params = {**base_params, 'methods': allowed_methods}
                if view is None and root:
                    view = method_not_allowed
            else:
                view = self._not_found
                params = {**base_params}
                if view is None and root:
                    view = not_found

        if view is None:
            raise NoView(allowed_methods)

        view = ResolvedView(view, params)
        for middleware in reversed(self._middlewares):
            view = middleware(view)
        return view

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
