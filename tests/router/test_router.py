import asyncio

import pytest

from jackie.router import Router
from jackie.http import asgi_to_jackie, JsonResponse, Request, TextResponse


app = Router()


# Post resource (full urls)

@app.get('/post/')
async def post_list(request):
    return TextResponse('post list')


@app.post('/post/')
async def post_create(request):
    return TextResponse('post create')


@app.get('/post/<post_id:int>/')
async def post_detail(request, post_id):
    return TextResponse(f'post detail {post_id}')


@app.put('/post/<post_id:int>/')
@app.patch('/post/<post_id:int>/')
async def post_update(request, post_id):
    return TextResponse(f'post update {post_id}')


@app.delete('/post/<post_id:int>/')
async def post_delete(request, post_id):
    return TextResponse(f'post delete {post_id}')


# User resource (included urls)

user_app = Router()


@user_app.get('')
async def user_list(request):
    return TextResponse('user list')


@user_app.post('')
async def user_create(request):
    return TextResponse('user create')


# Include in the middle so we can verify that routes before and after include
# work
app.include('/user/', user_app)


@user_app.get('<user_id:int>/')
async def user_detail(request, user_id):
    return TextResponse(f'user detail {user_id}')


@user_app.put('<user_id:int>/')
@user_app.patch('<user_id:int>/')
async def user_update(request, user_id):
    return TextResponse(f'user update {user_id}')


@user_app.delete('<user_id:int>/')
async def user_delete(request, user_id):
    return TextResponse(f'user delete {user_id}')


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
        return JsonResponse({'foo': 'bar'})

    @router.not_found
    async def not_found(request):
        return JsonResponse(
            status=404,
            body={
                'code': 'not_found',
                'message': 'Not Found',
            },
        )

    @router.method_not_allowed
    async def method_not_allowed(request, methods):
        return JsonResponse(
            status=405,
            body={
                'code': 'method_not_allowed',
                'message': 'Method Not Allowed',
            },
            allow=', '.join(sorted(methods))
        )

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


@pytest.mark.asyncio
async def test_post_asgi():
    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'http',
        'path': '/post/',
        'method': 'GET',
        'querystring': '',
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
        return TextResponse('get')

    @app.head('/')
    async def head_view(request):
        return TextResponse('head')

    @app.post('/')
    async def post_view(request):
        return TextResponse('post')

    @app.put('/')
    async def put_view(request):
        return TextResponse('put')

    @app.delete('/')
    async def delete_view(request):
        return TextResponse('delete')

    @app.connect('/')
    async def connect_view(request):
        return TextResponse('connect')

    @app.options('/')
    async def options_view(request):
        return TextResponse('options')

    @app.trace('/')
    async def trace_view(request):
        return TextResponse('trace')

    @app.patch('/')
    async def patch_view(request):
        return TextResponse('patch')

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
    @asgi_to_jackie
    async def echo(scope, receive, send):
        assert scope['type'] == 'websocket'
        assert await receive() == {'type': 'websocket.connect'}
        await send({'type': 'websocket.accept'})
        while True:
            message = await receive()
            if message['type'] == 'websocket.disconnect':
                break
            assert message['type'] == 'websocket.receive'
            await send({**message, 'type': 'websocket.send'})

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/',
    }
    task = asyncio.ensure_future(router(scope, input_queue.get, output_queue.put))

    await input_queue.put({'type': 'websocket.connect'})
    assert await output_queue.get() == {'type': 'websocket.accept'}
    await input_queue.put({'type': 'websocket.receive', 'text': 'foo'})
    assert await output_queue.get() == {'type': 'websocket.send', 'text': 'foo'}
    await input_queue.put({'type': 'websocket.receive', 'bytes': b'foo'})
    assert await output_queue.get() == {'type': 'websocket.send', 'bytes': b'foo'}
    await input_queue.put({'type': 'websocket.disconnect'})
    await task

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/foo',
    }
    task = asyncio.ensure_future(router(scope, input_queue.get, output_queue.put))

    await input_queue.put({'type': 'websocket.connect'})
    assert await output_queue.get() == {'type': 'websocket.close'}
    await task

    input_queue = asyncio.Queue()
    output_queue = asyncio.Queue()

    scope = {
        'type': 'websocket',
        'path': '/foo',
    }
    task = asyncio.ensure_future(router(scope, input_queue.get, output_queue.put))

    await input_queue.put({'type': 'websocket.send', 'text': 'too soon'})
    with pytest.raises(ValueError):
        await task
