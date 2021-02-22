import pytest

from jackie.http import Response, Cookie
from jackie.multipart import File


@pytest.mark.asyncio()
async def test_form_request():
    response = Response(form={
        'foo': '123',
        'bar': 'multi\nline\nstring',
        'baz': File('baz.png', 'image/png', b'pngcontent'),
    })
    assert response.content_type == 'multipart/form-data'
    boundary = response.boundary.encode()
    assert await response.body() == (
        b'--' + boundary + b'\n'
        b'Content-Disposition: form-data; name=foo\n'
        b'\n'
        b'123\n'
        b'--' + boundary + b'\n'
        b'Content-Disposition: form-data; name=bar\n'
        b'\n'
        b'multi\n'
        b'line\n'
        b'string\n'
        b'--' + boundary + b'\n'
        b'Content-Disposition: form-data; name=baz; filename=baz.png\n'
        b'Content-Type: image/png\n'
        b'\n'
        b'pngcontent\n'
        b'--' + boundary + b'--\n'
    )
    data = await response.form()
    assert set(data) == {'foo', 'bar', 'baz'}
    assert data['foo'] == '123'
    assert data['bar'] == 'multi\nline\nstring'
    assert data['baz'].content_type == 'image/png'
    assert data['baz'].content == b'pngcontent'


@pytest.mark.asyncio
async def test_html_response():
    response = Response(html='<p>foobar</p>')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=UTF-8'
    assert await response.body() == b'<p>foobar</p>'
    assert await response.text() == '<p>foobar</p>'


@pytest.mark.asyncio
async def test_json_response():
    response = Response(json={'foo': 'bar'})
    assert response.status == 200
    assert response.headers['Content-Type'] == (
        'application/json; charset=UTF-8'
    )
    assert await response.body() == b'{"foo": "bar"}'
    assert await response.text() == '{"foo": "bar"}'


@pytest.mark.asyncio
async def test_redirect_response():
    response = Response(redirect='https://www.foobar.test/')
    assert response.status == 304
    assert response.headers['Location'] == 'https://www.foobar.test/'
    assert await response.body() == b''


@pytest.mark.asyncio
async def test_text_response():
    response = Response(text='foobar')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/plain; charset=UTF-8'
    assert await response.body() == b'foobar'
    assert await response.text() == 'foobar'


def test_multi():
    with pytest.raises(ValueError):
        Response(text='foobar', body=b'foobar')


def test_ok():
    assert Response(status=200).ok
    assert Response(status=301).ok
    assert not Response(status=400).ok
    assert not Response(status=500).ok


def test_set_cookies():
    response = Response(set_cookies=[
        Cookie('foo', 'bar'),
        Cookie('bar', 'baz"qux'),
    ])
    assert response.headers.getlist('Set-Cookie') == [
        'foo=bar',
        'bar="baz\\"qux"',
    ]
