import pytest

from jack.router import Router
from jack.http import asgi_to_jack, Request, TextResponse


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
view = asgi_to_jack(app)


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
