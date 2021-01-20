import pytest

from jackie.http import JsonRequest, TextRequest


@pytest.mark.asyncio
async def test_json_request():
    request = JsonRequest(body={'foo': 'bar'})
    assert await request.body() == b'{"foo": "bar"}'
    assert await request.json() == {'foo': 'bar'}


@pytest.mark.asyncio
async def test_text_request():
    request = TextRequest(body='foobar')
    assert await request.body() == b'foobar'
    assert await request.text() == 'foobar'
