import pytest

from jackie.router import Router
from jackie.http import Response, TextResponse
from jackie.http.exceptions import Disconnect
from jackie.client import Client
from jackie.multipart import File


app = Router()


@app.get('/')
async def hello_world(request):
    name = request.query.get('name', 'World')
    return TextResponse(f'Hello, {name}!')


@app.get('/echo')
async def echo(request):
    return Response(request.chunks(), headers=request.headers)


@app.websocket('/echo')
async def echo_websocket(socket):
    await socket.accept()
    while True:
        try:
            message = await socket.receive_bytes()
        except Disconnect:
            break
        await socket.send_bytes(message)


@app.websocket('/accept-and-close')
async def accept_and_close_websocket(socket):
    await socket.accept()
    await socket.close()


@app.websocket('/exit-early')
async def exit_early_websocket(socket):
    return


@app.websocket('/crash')
async def crash_websocket(socket):
    raise ValueError('test exception')


@app.websocket('/accept-and-exit-early')
async def accept_and_exit_early_websocket(socket):
    await socket.accept()


@app.websocket('/early-send')
async def early_send_websocket(socket):
    await socket.send_text('foobar')


@app.websocket('/early-receive')
async def early_receive_websocket(socket):
    await socket.receive_text()


@app.websocket('/double-close')
async def double_close_websocket(socket):
    await socket.close()
    await socket.close()


@app.websocket('/double-accept')
async def double_accept_websocket(socket):
    await socket.accept()
    await socket.accept()


@app.get('/get')
async def get_view(request):
    return TextResponse('get')


@app.head('/head')
async def head_view(request):
    return TextResponse('head')


@app.post('/post')
async def post_view(request):
    return TextResponse('post')


@app.put('/put')
async def put_view(request):
    return TextResponse('put')


@app.delete('/delete')
async def delete_view(request):
    return TextResponse('delete')


@app.connect('/connect')
async def connect_view(request):
    return TextResponse('connect')


@app.options('/options')
async def options_view(request):
    return TextResponse('options')


@app.trace('/trace')
async def trace_view(request):
    return TextResponse('trace')


@app.patch('/patch')
async def patch_view(request):
    return TextResponse('patch')


@pytest.mark.asyncio
async def test_client():
    client = Client(app)

    res = await client.get('/')
    assert res.ok
    assert await res.text() == 'Hello, World!'

    res = await client.get('/', query={'name': 'test'})
    assert res.ok
    assert await res.text() == 'Hello, test!'


@pytest.mark.asyncio
async def test_form_body():
    client = Client(app)
    res = await client.get('/echo', form={
        'foo': 'foo',
        'bar': File('bar.txt', 'text/plain', b'bar'),
    })
    assert res.ok
    assert res.content_type == 'multipart/form-data'
    form = await res.form()
    assert set(form) == {'foo', 'bar'}
    assert form['foo'] == 'foo'
    assert isinstance(form['bar'], File)
    assert form['bar'].name == 'bar.txt'
    assert form['bar'].content_type == 'text/plain'
    assert form['bar'].content == b'bar'


@pytest.mark.asyncio
async def test_json_body():
    client = Client(app)
    res = await client.get('/echo', json={'foo': True, 'bar': [1, 2, 3]})
    assert res.ok
    assert res.content_type == 'application/json'
    assert await res.json() == {'foo': True, 'bar': [1, 2, 3]}


@pytest.mark.asyncio
async def test_text_body():
    client = Client(app)
    res = await client.get('/echo', text='foobar')
    assert res.ok
    assert res.content_type == 'text/plain'
    assert await res.text() == 'foobar'


@pytest.mark.asyncio
async def test_binary_body():
    client = Client(app)
    res = await client.get('/echo', body=b'foobar')
    assert res.ok
    assert res.content_type is None
    assert await res.body() == b'foobar'


@pytest.mark.asyncio
async def test_multiple_bodies():
    client = Client(app)
    with pytest.raises(ValueError):
        await client.get(text='foobar', body=b'foobar')


@pytest.mark.asyncio
async def test_get():
    client = Client(app)
    res = await client.get('/get')
    assert res.ok
    assert await res.text() == 'get'


@pytest.mark.asyncio
async def test_head():
    client = Client(app)
    res = await client.head('/head')
    assert res.ok
    assert await res.text() == 'head'


@pytest.mark.asyncio
async def test_post():
    client = Client(app)
    res = await client.post('/post')
    assert res.ok
    assert await res.text() == 'post'


@pytest.mark.asyncio
async def test_put():
    client = Client(app)
    res = await client.put('/put')
    assert res.ok
    assert await res.text() == 'put'


@pytest.mark.asyncio
async def test_delete():
    client = Client(app)
    res = await client.delete('/delete')
    assert res.ok
    assert await res.text() == 'delete'


@pytest.mark.asyncio
async def test_connect():
    client = Client(app)
    res = await client.connect('/connect')
    assert res.ok
    assert await res.text() == 'connect'


@pytest.mark.asyncio
async def test_options():
    client = Client(app)
    res = await client.options('/options')
    assert res.ok
    assert await res.text() == 'options'


@pytest.mark.asyncio
async def test_trace():
    client = Client(app)
    res = await client.trace('/trace')
    assert res.ok
    assert await res.text() == 'trace'


@pytest.mark.asyncio
async def test_patch():
    client = Client(app)
    res = await client.patch('/patch')
    assert res.ok
    assert await res.text() == 'patch'


@pytest.mark.asyncio
async def test_websocket():
    client = Client(app)
    socket = await client.websocket('/echo')
    await socket.accepted()
    await socket.send_text('foo')
    assert await socket.receive_text() == 'foo'
    await socket.send_text('bar')
    assert await socket.receive_text() == 'bar'
    await socket.close()


@pytest.mark.asyncio
async def test_auto_close_socket():
    client = Client(app)
    socket = await client.websocket('/echo')
    await socket.accepted()


@pytest.mark.asyncio
async def test_websocket_accept():
    client = Client(app)
    socket = await client.websocket('/does-not-exist')
    with pytest.raises(ValueError):
        await socket.accept()


@pytest.mark.asyncio
async def test_websocket_accepted_after_close():
    client = Client(app)
    socket = await client.websocket('/does-not-exist')
    await socket.closed()
    with pytest.raises(ValueError):
        await socket.accepted()


@pytest.mark.asyncio
async def test_websocket_closed_after_close():
    client = Client(app)
    socket = await client.websocket('/does-not-exist')
    await socket.closed()
    with pytest.raises(ValueError):
        await socket.closed()


@pytest.mark.asyncio
async def test_websocket_receive_text_after_close():
    client = Client(app)
    socket = await client.websocket('/does-not-exist')
    await socket.closed()
    with pytest.raises(ValueError):
        await socket.receive_text()


@pytest.mark.asyncio
async def test_websocket_send_text_after_close():
    client = Client(app)
    socket = await client.websocket('/does-not-exist')
    await socket.closed()
    with pytest.raises(ValueError):
        await socket.send_text('foo')


@pytest.mark.asyncio
async def test_websocket_close_after_close():
    client = Client(app)
    socket = await client.websocket('/does-not-exist')
    await socket.closed()
    with pytest.raises(ValueError):
        await socket.close()


@pytest.mark.asyncio
async def test_websocket_closed_when_accepted():
    client = Client(app)
    socket = await client.websocket('/echo')
    with pytest.raises(AssertionError):
        await socket.closed()


@pytest.mark.asyncio
async def test_websocket_accepted_when_closed():
    client = Client(app)
    socket = await client.websocket('/does-not-exist')
    with pytest.raises(Disconnect):
        await socket.accepted()


@pytest.mark.asyncio
async def test_websocket_closed():
    client = Client(app)
    socket = await client.websocket('/does-not-exist')
    await socket.closed()


@pytest.mark.asyncio
async def test_accept_and_close():
    client = Client(app)
    socket = await client.websocket('/accept-and-close')
    await socket.accepted()
    await socket.closed()


@pytest.mark.asyncio
async def test_websocket_receive_during_close():
    client = Client(app)
    socket = await client.websocket('/accept-and-close')
    await socket.accepted()
    with pytest.raises(Disconnect):
        await socket.receive_text()


@pytest.mark.asyncio
async def test_websocket_send_during_close():
    client = Client(app)
    socket = await client.websocket('/accept-and-close')
    await socket.accepted()


@pytest.mark.asyncio
async def test_accepted_when_exit_early():
    client = Client(app)
    socket = await client.websocket('/exit-early')
    with pytest.raises(ValueError):
        await socket.accepted()


@pytest.mark.asyncio
async def test_closed_when_exit_early():
    client = Client(app)
    socket = await client.websocket('/exit-early')
    with pytest.raises(ValueError):
        await socket.closed()


@pytest.mark.asyncio
async def test_send_when_accepted_and_exit_early():
    client = Client(app)
    socket = await client.websocket('/accept-and-exit-early')
    await socket.accepted()
    with pytest.raises(ValueError):
        await socket.send_text('foo')


@pytest.mark.asyncio
async def test_receive_when_accepted_and_exit_early():
    client = Client(app)
    socket = await client.websocket('/accept-and-exit-early')
    await socket.accepted()
    with pytest.raises(ValueError):
        await socket.receive_text()


@pytest.mark.asyncio
async def test_websocket_crash_on_accepted():
    client = Client(app)
    socket = await client.websocket('/crash')
    with pytest.raises(ValueError) as exc_info:
        await socket.accepted()
    assert str(exc_info.value) == 'test exception'


@pytest.mark.asyncio
async def test_websocket_crash_on_close():
    client = Client(app)
    socket = await client.websocket('/crash')
    with pytest.raises(ValueError) as exc_info:
        await socket.close()
    assert str(exc_info.value) == 'test exception'


@pytest.mark.asyncio
async def test_websocket_early_send():
    client = Client(app)
    socket = await client.websocket('/early-send')
    with pytest.raises(ValueError):
        await socket.accepted()


@pytest.mark.asyncio
async def test_websocket_early_receive():
    client = Client(app)
    socket = await client.websocket('/early-receive')
    with pytest.raises(ValueError):
        await socket.accepted()


@pytest.mark.asyncio
async def test_websocket_double_close():
    client = Client(app)
    socket = await client.websocket('/double-close')
    await socket.closed()
    with pytest.raises(ValueError):
        await socket.closed()


@pytest.mark.asyncio
async def test_websocket_double_accept():
    client = Client(app)
    socket = await client.websocket('/double-accept')
    await socket.accepted()
    with pytest.raises(ValueError):
        await socket.accepted()
