import pytest

from jackie.http import (
    HtmlResponse, JsonResponse, RedirectResponse, TextResponse,
)


@pytest.mark.asyncio
async def test_html_response():
    response = HtmlResponse('<p>foobar</p>')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/html; charset=UTF-8'
    assert await response.body() == b'<p>foobar</p>'
    assert await response.text() == '<p>foobar</p>'


@pytest.mark.asyncio
async def test_json_response():
    response = JsonResponse({'foo': 'bar'})
    assert response.status == 200
    assert response.headers['Content-Type'] == (
        'application/json; charset=UTF-8'
    )
    assert await response.body() == b'{"foo": "bar"}'
    assert await response.text() == '{"foo": "bar"}'


@pytest.mark.asyncio
async def test_redirect_response():
    response = RedirectResponse('https://www.foobar.test/')
    assert response.status == 304
    assert response.headers['Location'] == 'https://www.foobar.test/'
    assert await response.body() == b''


@pytest.mark.asyncio
async def test_text_response():
    response = TextResponse('foobar')
    assert response.status == 200
    assert response.headers['Content-Type'] == 'text/plain; charset=UTF-8'
    assert await response.body() == b'foobar'
    assert await response.text() == 'foobar'
