import pytest

from jackie.http import Cookie, Socket


def test_cookies():
    request = Socket(
        accept=None, close=None, receive=None, send=None,
        Cookie='foo=bar; bar="baz\\"qux"',
    )
    assert request.cookies == {
        'foo': 'bar',
        'bar': 'baz"qux',
    }


@pytest.mark.asyncio
async def test_set_cookies():
    headers = None

    async def accept(headers_):
        nonlocal headers
        headers = headers_

    socket = Socket(accept=accept, close=None, receive=None, send=None)
    await socket.accept(set_cookies=[
        Cookie('foo', 'bar'),
        Cookie('bar', 'baz"qux'),
    ])

    assert headers.getlist('Set-Cookie') == [
        'foo=bar',
        'bar="baz\\"qux"',
    ]


@pytest.mark.asyncio
async def test_unset_cookies():
    headers = None

    async def accept(headers_):
        nonlocal headers
        headers = headers_

    socket = Socket(accept=accept, close=None, receive=None, send=None)
    await socket.accept(
        set_cookies=[Cookie('foo', 'bar')],
        unset_cookies=['foo'],
    )

    assert headers.getlist('Set-Cookie') == [
        'foo=bar',
        'foo=""; Expires=Thu, 1 Jan 1970 00:00:00 GMT',
    ]
