import tempfile

import pytest

from jackie.http import Request
from jackie.multipart import File


@pytest.mark.asyncio()
async def test_form_request():
    request = Request(form={
        'foo': '123',
        'bar': 'multi\nline\nstring',
        'baz': File('baz.png', 'image/png', b'pngcontent'),
    })
    assert request.content_type == 'multipart/form-data'
    boundary = request.boundary.encode()
    assert await request.body() == (
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
    data = await request.form()
    assert set(data) == {'foo', 'bar', 'baz'}
    assert data['foo'] == '123'
    assert data['bar'] == 'multi\nline\nstring'
    assert data['baz'].content_type == 'image/png'
    assert data['baz'].content == b'pngcontent'


@pytest.mark.asyncio
async def test_json_request():
    request = Request(json={'foo': 'bar'})
    assert request.content_type == 'application/json'
    assert request.charset == 'UTF-8'
    assert await request.body() == b'{"foo": "bar"}'
    assert await request.json() == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_text_request():
    request = Request(text='foobar')
    assert request.content_type == 'text/plain'
    assert request.charset == 'UTF-8'
    assert await request.body() == b'foobar'
    assert await request.text() == 'foobar'


@pytest.mark.asyncio
async def test_file_request():
    with tempfile.NamedTemporaryFile(suffix='.txt') as f:
        f.write(b'foobar')
        f.flush()

        request = Request(file=f.name)
        assert request.content_type == 'text/plain'
        assert await request.body() == b'foobar'
        assert await request.text() == 'foobar'


@pytest.mark.asyncio
async def test_multipart_file_request():
    request = Request(file=File('foo.txt', 'text/plain', b'foobar'))
    assert request.content_type == 'text/plain'
    assert await request.body() == b'foobar'
    assert await request.text() == 'foobar'


def test_cookies():
    request = Request(Cookie='foo=bar; bar="baz\\"qux"')
    assert request.cookies == {
        'foo': 'bar',
        'bar': 'baz"qux',
    }
