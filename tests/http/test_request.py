import pytest

from jackie.http import FormRequest, JsonRequest, TextRequest
from jackie.multipart import File


@pytest.mark.asyncio()
async def test_form_request():
    request = FormRequest(body={
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
    assert await data['baz'].body() == b'pngcontent'


@pytest.mark.asyncio
async def test_json_request():
    request = JsonRequest(body={'foo': 'bar'})
    assert request.content_type == 'application/json'
    assert request.charset == 'UTF-8'
    assert await request.body() == b'{"foo": "bar"}'
    assert await request.json() == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_text_request():
    request = TextRequest(body='foobar')
    assert request.content_type == 'text/plain'
    assert request.charset == 'UTF-8'
    assert await request.body() == b'foobar'
    assert await request.text() == 'foobar'
