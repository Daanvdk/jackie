from datetime import datetime, timezone

from jackie.serialize import serialize_set_cookie


def test_serialize_set_cookie():
    name = 'sessionId'
    value = '38afes7a8'
    params = {'secure': False, 'http_only': False}
    assert serialize_set_cookie(name, value, params) == 'sessionId=38afes7a8'


def test_serialize_set_cookie_expires():
    name = 'id'
    value = 'a3fWa'
    params = {
        'secure': False,
        'http_only': False,
        'expires': datetime(2015, 10, 21, 7, 28, 0, tzinfo=timezone.utc),
    }
    assert serialize_set_cookie(name, value, params) == (
        'id=a3fWa; Expires=Wed, 21 Oct 2015 07:28:00 GMT'
    )


def test_serialize_set_cookie_max_age():
    name = 'id'
    value = 'a3fWa'
    params = {'secure': False, 'http_only': False, 'max_age': 2592000}
    assert serialize_set_cookie(name, value, params) == (
        'id=a3fWa; Max-Age=2592000'
    )


def test_serialize_set_cookie_domain():
    name = 'qwerty'
    value = '219ffwef9w0f'
    params = {
        'secure': False,
        'http_only': False,
        'domain': 'somecompany.co.uk',
    }
    assert serialize_set_cookie(name, value, params) == (
        'qwerty=219ffwef9w0f; Domain=somecompany.co.uk'
    )


def test_serialize_set_cookie_domain_2():
    name = 'sessionId'
    value = 'e8bb43229de9'
    params = {'secure': False, 'http_only': False, 'domain': 'foo.example.com'}
    assert serialize_set_cookie(name, value, params) == (
        'sessionId=e8bb43229de9; Domain=foo.example.com'
    )


def test_serialize_set_cookie_path():
    name = 'cookie'
    value = '123'
    params = {'secure': False, 'http_only': False, 'path': '/foo/bar'}
    assert serialize_set_cookie(name, value, params) == (
        'cookie=123; Path=/foo/bar'
    )


def test_serialize_set_cookie_path_string():
    name = 'cookie'
    value = '123'
    params = {'secure': False, 'http_only': False, 'path': 'foo"bar'}
    assert serialize_set_cookie(name, value, params) == (
        'cookie=123; Path="foo\\"bar"'
    )


def test_serialize_set_cookie_secure():
    name = 'cookie'
    value = '123'
    params = {'secure': True, 'http_only': False}
    assert serialize_set_cookie(name, value, params) == 'cookie=123; Secure'


def test_serialize_set_cookie_http_only():
    name = 'cookie'
    value = '123'
    params = {'secure': False, 'http_only': True}
    assert serialize_set_cookie(name, value, params) == 'cookie=123; HttpOnly'


def test_serialize_set_cookie_same_site_lax():
    name = 'cookie'
    value = '123'
    params = {'secure': False, 'http_only': False, 'same_site': 'lax'}
    assert serialize_set_cookie(name, value, params) == (
        'cookie=123; SameSite=Lax'
    )


def test_serialize_set_cookie_same_site_strict():
    name = 'cookie'
    value = '123'
    params = {'secure': False, 'http_only': False, 'same_site': 'strict'}
    assert serialize_set_cookie(name, value, params) == (
        'cookie=123; SameSite=Strict'
    )


def test_serialize_set_cookie_same_site_none():
    name = 'cookie'
    value = '123'
    params = {'secure': False, 'http_only': False, 'same_site': 'none'}
    assert serialize_set_cookie(name, value, params) == (
        'cookie=123; SameSite=None'
    )
