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

    def __init__(self, router, name, params, view):
        super().__init__(ResolvedApp(self))
        self.router = router
        self.name = name
        self.params = params
        self.view = view

    async def __call__(self, request, **params):
        request.router = self.router
        request.view_name = self.name
        return await self.view(request, **self.params)


class ResolvedApp(JackieToAsgi):

    async def __call__(self, scope, receive, send):
        app = jackie_to_asgi(self.view.view)
        scope = {**scope, 'jackie.router': {
            'router': self.view.router,
            'name': self.view.name,
            'params': self.view.params,
        }}
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

    def route(self, methods, matcher, view=None, *, name=None):
        if view is None:
            def decorator(view):
                self.route(methods, matcher, view, name=name)
                return view
            return decorator
        if isinstance(methods, str):
            methods = {methods}
        if not isinstance(matcher, Matcher):
            matcher = Matcher(matcher)
        self._routes.append((methods, matcher, view, name))
        return self

    def include(self, matcher, router, *, name=None):
        if not isinstance(matcher, Matcher):
            matcher = Matcher(matcher)
        self._routes.append((None, matcher, router, name))
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

    def _get_view(
        self, method, path,
        *, base_router=None, base_name='', base_params={},
    ):
        allowed_methods = set()

        if base_router is None:
            base_router = self

        for methods, matcher, view, name in self._routes:
            if methods is None:
                try:
                    params, path = matcher.match(path)
                except Matcher.Error:
                    continue
                try:
                    view = view._get_view(
                        method, path,
                        base_router=base_router,
                        base_name=(
                            base_name + name + ':'
                            if name is not None else
                            base_name
                        ),
                        base_params={**base_params, **params},
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
                    view = ResolvedView(
                        router=base_router,
                        name=base_name + name if name is not None else None,
                        params={**base_params, **params},
                        view=view,
                    )
                    break
            allowed_methods.update(methods)
        else:
            if method == 'WEBSOCKET':
                view = self._websocket_not_found
                params = {**base_params}
                if view is None and base_router is self:
                    view = websocket_not_found
            elif allowed_methods:
                view = self._method_not_allowed
                params = {**base_params, 'methods': allowed_methods}
                if view is None and base_router is self:
                    view = method_not_allowed
            else:
                view = self._not_found
                params = {**base_params}
                if view is None and base_router is self:
                    view = not_found
            if view is not None:
                view = ResolvedView(base_router, None, params, view)

        if view is None:
            raise NoView(allowed_methods)

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

    def _get_matcher(self, name):
        for methods, matcher, view, name_ in self._routes:
            if methods is None:
                if name_ is not None and not name.startswith(name_ + ':'):
                    continue
                try:
                    return matcher + view._get_matcher(
                        name if name_ is None else name[len(name_) + 1:],
                    )
                except ValueError:
                    pass
            elif name_ == name:
                return matcher
        raise ValueError('unknown name')

    def reverse(self, name, **params):
        return self._get_matcher(name).reverse(**params)


class JackieRouter(AsgiToJackie):

    async def __call__(self, request, **params):
        view = self.app._get_view(request.method, request.path)
        return await view(request, **params)
