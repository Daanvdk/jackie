import asyncio

import pytest

from jackie.router import Router
from jackie.http import asgi_to_jackie, Request, Response
from jackie.http.exceptions import Disconnect


app = Router()


# Post resource (full urls)

@app.get('/post/', name='post:list')
async def post_list(request):
    return Response(text='post list')


@app.post('/post/', name='post:create')
async def post_create(request):
    return Response(text='post create')


@app.get('/post/<post_id:int>/', name='post:detail')
async def post_detail(request, post_id):
    return Response(text=f'post detail {post_id}')


@app.put('/post/<post_id:int>/', name='post:update')
@app.patch('/post/<post_id:int>/')
async def post_update(request, post_id):
    return Response(text=f'post update {post_id}')


@app.delete('/post/<post_id:int>/', name='post:delete')
async def post_delete(request, post_id):
    return Response(text=f'post delete {post_id}')


# User resource (included urls)

user_app = Router()


@user_app.get('', name='list')
async def user_list(request):
    return Response(text='user list')


@user_app.post('', name='create')
async def user_create(request):
    return Response(text='user create')


# Include in the middle so we can verify that routes before and after include
# work
app.include('/user/', user_app, name='user')


@user_app.get('<user_id:int>/', name='detail')
async def user_detail(request, user_id):
    return Response(text=f'user detail {user_id}')


@user_app.put('<user_id:int>/', name='update')
@user_app.patch('<user_id:int>/', name='update')
async def user_update(request, user_id):
    return Response(text=f'user update {user_id}')


@user_app.delete('<user_id:int>/', name='delete')
async def user_delete(request, user_id):
    return Response(text=f'user delete {user_id}')


# Easier to test
view = asgi_to_jackie(app)


@pytest.mark.asyncio
async def test_post():
    response = await view(Request(method='GET', path='/post/'))
    assert response.status == 200
    assert await response.text() == 'post list'

    response = await view(Request(method='POST', path='/post/'))
    assert response.status == 200
    assert await response.text() == 'post create'

    response = await view(Request(method='PUT', path='/post/'))
    assert response.status == 405
    assert response.headers['Allow'] == 'GET, POST'
    assert await response.text() == 'Method Not Allowed'

    response = await view(Request(method='GET', path='/post/123/'))
    assert response.status == 200
    assert await response.text() == 'post detail 123'

    response = await view(Request(method='PUT', path='/post/123/'))
    assert response.status == 200
    assert await response.text() == 'post update 123'

    response = await view(Request(method='PATCH', path='/post/123/'))
    assert response.status == 200
    assert await response.text() == 'post update 123'

    response = await view(Request(method='DELETE', path='/post/123/'))
    assert response.status == 200
    assert await response.text() == 'post delete 123'

    response = await view(Request(method='POST', path='/post/123/'))
    assert response.status == 405
    assert response.headers['Allow'] == 'DELETE, GET, PATCH, PUT'
    assert await response.text() == 'Method Not Allowed'


@pytest.mark.asyncio
async def test_user():
    response = await view(Request(method='GET', path='/user/'))
    assert response.status == 200
    assert await response.text() == 'user list'

    response = await view(Request(method='POST', path='/user/'))
    assert response.status == 200
    assert await response.text() == 'user create'

    response = await view(Request(method='PUT', path='/user/'))
    assert response.status == 405
    assert response.headers['Allow'] == 'GET, POST'
    assert await response.text() == 'Method Not Allowed'

    response = await view(Request(method='GET', path='/user/123/'))
    assert response.status == 200
    assert await response.text() == 'user detail 123'

    response = await view(Request(method='PUT', path='/user/123/'))
    assert response.status == 200
    assert await response.text() == 'user update 123'

    response = await view(Request(method='PATCH', path='/user/123/'))
    assert response.status == 200
    assert await response.text() == 'user update 123'

    response = await view(Request(method='DELETE', path='/user/123/'))
    assert response.status == 200
    assert await response.text() == 'user delete 123'

    response = await view(Request(method='POST', path='/user/123/'))
    assert response.status == 405
    assert response.headers['Allow'] == 'DELETE, GET, PATCH, PUT'
    assert await response.text() == 'Method Not Allowed'

    response = await view(Request(method='POST', path='/user/foo/'))
    assert response.status == 404
    assert await response.text() == 'Not Found'


@pytest.mark.asyncio
async def test_custom_error_pages():
    router = Router()

    @router.get('/api/')
    async def foo(request):
        return Response(json={'foo': 'bar'})

    @router.not_found
    async def not_found(request):
        return Response(
            status=404,
            json={
                'code': 'not_found',
                'message': 'Not Found',
            },
        )

    @router.method_not_allowed
    async def method_not_allowed(request, methods):
        return Response(
            status=405,
            json={
                'code': 'method_not_allowed',
                'message': 'Method Not Allowed',
            },
            allow=', '.join(sorted(methods))
        )

    @router.websocket_not_found
    async def websocket_not_found(socket):
        await socket.close(1337)

    view = asgi_to_jackie(router)

    response = await view(Request(method='GET', path='/api/'))
    assert response.status == 200
    assert await response.json() == {'foo': 'bar'}

    response = await view(Request(method='GET', path='/other/'))
    assert response.status == 404
    assert await response.json() == {
        'code': 'not_found',
        'message': 'Not Found',
    }

    response = await view(Request(method='POST', path='/api/'))
    assert response.status == 405
    assert await response.json() == {
        'code': 'method_not_allowed',
        'message': 'Method Not Allowed',
    }

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/api/',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(
        router(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    assert await output_queue.get() == {
        'type': 'websocket.close',
        'code': 1337,
    }
    await task

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/other/',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(
        router(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    assert await output_queue.get() == {
        'type': 'websocket.close',
        'code': 1337,
    }
    await task


@pytest.mark.asyncio
async def test_post_asgi():
    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'http',
        'path': '/post/',
        'method': 'GET',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(app(scope, input_queue.get, output_queue.put))

    assert await output_queue.get() == {
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            (b'content-type', b'text/plain; charset=UTF-8'),
        ],
    }
    assert await output_queue.get() == {
        'type': 'http.response.body',
        'body': b'post list',
        'more_body': True,
    }
    assert await output_queue.get() == {
        'type': 'http.response.body',
        'body': b'',
        'more_body': False,
    }

    await task


@pytest.mark.asyncio
async def test_router_unusual_scope():
    with pytest.raises(ValueError):
        await app({'type': 'unusual'}, None, None)


@pytest.mark.asyncio
async def test_all_methods():
    app = Router()

    @app.get('/')
    async def get_view(request):
        return Response(text='get')

    @app.head('/')
    async def head_view(request):
        return Response(text='head')

    @app.post('/')
    async def post_view(request):
        return Response(text='post')

    @app.put('/')
    async def put_view(request):
        return Response(text='put')

    @app.delete('/')
    async def delete_view(request):
        return Response(text='delete')

    @app.connect('/')
    async def connect_view(request):
        return Response(text='connect')

    @app.options('/')
    async def options_view(request):
        return Response(text='options')

    @app.trace('/')
    async def trace_view(request):
        return Response(text='trace')

    @app.patch('/')
    async def patch_view(request):
        return Response(text='patch')

    view = asgi_to_jackie(app)

    response = await view(Request(method='GET', path='/'))
    assert response.status == 200
    assert await response.text() == 'get'

    response = await view(Request(method='HEAD', path='/'))
    assert response.status == 200
    assert await response.text() == 'head'

    response = await view(Request(method='POST', path='/'))
    assert response.status == 200
    assert await response.text() == 'post'

    response = await view(Request(method='PUT', path='/'))
    assert response.status == 200
    assert await response.text() == 'put'

    response = await view(Request(method='DELETE', path='/'))
    assert response.status == 200
    assert await response.text() == 'delete'

    response = await view(Request(method='CONNECT', path='/'))
    assert response.status == 200
    assert await response.text() == 'connect'

    response = await view(Request(method='OPTIONS', path='/'))
    assert response.status == 200
    assert await response.text() == 'options'

    response = await view(Request(method='TRACE', path='/'))
    assert response.status == 200
    assert await response.text() == 'trace'

    response = await view(Request(method='PATCH', path='/'))
    assert response.status == 200
    assert await response.text() == 'patch'


@pytest.mark.asyncio
async def test_websocket_route():
    router = Router()

    @router.websocket('/')
    async def echo(socket):
        await socket.accept()
        while True:
            try:
                message = await socket.receive_bytes()
            except Disconnect:
                break
            await socket.send_bytes(message)

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(
        router(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({
        'type': 'websocket.connect',
    })
    assert await output_queue.get() == {
        'type': 'websocket.accept',
        'headers': [],
    }
    await input_queue.put({
        'type': 'websocket.receive',
        'text': 'foo',
    })
    assert await output_queue.get() == {
        'type': 'websocket.send',
        'bytes': b'foo',
        'text': None,
    }
    await input_queue.put({
        'type': 'websocket.receive',
        'bytes': b'foo',
    })
    assert await output_queue.get() == {
        'type': 'websocket.send',
        'bytes': b'foo',
        'text': None,
    }
    await input_queue.put({'type': 'websocket.disconnect'})
    await task

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/foo',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(
        router(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.connect'})
    assert await output_queue.get() == {
        'type': 'websocket.close',
        'code': 1000,
    }
    await task

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/foo',
        'query_string': b'',
        'headers': [],
    }
    task = asyncio.ensure_future(
        router(scope, input_queue.get, output_queue.put)
    )

    await input_queue.put({'type': 'websocket.send', 'text': 'too soon'})
    with pytest.raises(ValueError):
        await task


@pytest.mark.asyncio
async def test_middleware():
    router = Router()

    @router.get('/foo/')
    async def foo(request):
        return Response(text='foo')

    @router.get('/foo/<param>/')
    async def bar(request, param):
        return Response(text=param)

    @router.middleware
    def prefix_content(get_response):
        async def view(request):
            response = await get_response(request)
            try:
                prefix = request.query['prefix']
            except KeyError:
                pass
            else:
                response = Response(text=prefix + await response.text())
            return response
        return view

    view = asgi_to_jackie(router)

    response = await view(Request('/foo/'))
    assert response.status == 200
    assert await response.text() == 'foo'

    response = await view(Request('/foo/', query={'prefix': 'prefixed '}))
    assert response.status == 200
    assert await response.text() == 'prefixed foo'

    response = await view(Request('/foo/bar/'))
    assert response.status == 200
    assert await response.text() == 'bar'

    response = await view(Request('/foo/bar/', query={'prefix': 'prefixed '}))
    assert response.status == 200
    assert await response.text() == 'prefixed bar'


def test_reverse():
    assert app.reverse('post:list') == '/post/'
    assert app.reverse('post:create') == '/post/'

    assert app.reverse('post:detail', post_id=123) == '/post/123/'
    with pytest.raises(KeyError):
        app.reverse('post:detail')
    assert app.reverse('post:update', post_id=123) == '/post/123/'
    with pytest.raises(KeyError):
        app.reverse('post:update')
    assert app.reverse('post:delete', post_id=123) == '/post/123/'
    with pytest.raises(KeyError):
        app.reverse('post:delete')

    assert app.reverse('user:list') == '/user/'
    assert app.reverse('user:create') == '/user/'

    assert app.reverse('user:detail', user_id=123) == '/user/123/'
    with pytest.raises(KeyError):
        app.reverse('user:detail')
    assert app.reverse('user:update', user_id=123) == '/user/123/'
    with pytest.raises(KeyError):
        app.reverse('user:update')
    assert app.reverse('user:delete', user_id=123) == '/user/123/'
    with pytest.raises(KeyError):
        app.reverse('user:delete')

    with pytest.raises(ValueError):
        app.reverse('unknown')
    with pytest.raises(ValueError):
        app.reverse('user:unknown')
