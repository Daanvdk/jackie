from datetime import datetime, timezone

import pytest

from jackie.parse import (
    parse_content_disposition, parse_content_type, parse_cookies,
    parse_set_cookie,
)


def test_parse_content_disposition():
    value, params = parse_content_disposition('form-data; name=foo')
    assert value == 'form-data'
    assert params == {'name': 'foo'}


def test_parse_content_disposition_no_param_value():
    with pytest.raises(ValueError) as exc_info:
        parse_content_disposition('form-data; name=')
    assert str(exc_info.value) == (
        '16: got \'end\', expected \'name\' or \'string\''
    )


def test_parse_content_disposition_string_value():
    value, params = parse_content_disposition('form-data; name="foo \\" bar"')
    assert value == 'form-data'
    assert params == {'name': 'foo " bar'}


def test_parse_content_disposition_string_value_unterminated():
    with pytest.raises(ValueError) as exc_info:
        parse_content_disposition('form-data; name="foo \\" bar')
    assert str(exc_info.value) == (
        '27: got \'unterminated_string\', expected \'name\' or \'string\''
    )


def test_parse_content_type():
    value, params = parse_content_type('image/png')
    assert value == 'image/png'
    assert params == {}


def test_parse_cookies():
    cookies = parse_cookies('foo=123; bar="foo bar baz"; baz=qux')
    assert cookies == {
        'foo': '123',
        'bar': 'foo bar baz',
        'baz': 'qux',
    }


def test_parse_cookies_empty():
    cookies = parse_cookies('')
    assert cookies == {}


def test_parse_cookies_trailing_semicolon():
    cookies = parse_cookies('foo=1; bar=2; baz=3;')
    assert cookies == {
        'foo': '1',
        'bar': '2',
        'baz': '3',
    }


def test_parse_set_cookie():
    name, value, params = parse_set_cookie('sessionId=38afes7a8')
    assert name == 'sessionId'
    assert value == '38afes7a8'
    assert params == {'secure': False, 'http_only': False}


def test_parse_set_cookie_expires():
    name, value, params = parse_set_cookie(
        'id=a3fWa; Expires=Wed, 21 Oct 2015 07:28:00 GMT'
    )
    assert name == 'id'
    assert value == 'a3fWa'
    assert params == {
        'secure': False,
        'http_only': False,
        'expires': datetime(2015, 10, 21, 7, 28, 0, tzinfo=timezone.utc),
    }


def test_parse_set_cookie_expires_invalid():
    with pytest.raises(ValueError):
        parse_set_cookie('id=a3fWa; Expires=Thu, 21 Oct 2015 07:28:00 GMT')


def test_parse_set_cookie_max_age():
    name, value, params = parse_set_cookie('id=a3fWa; Max-Age=2592000')
    assert name == 'id'
    assert value == 'a3fWa'
    assert params == {'secure': False, 'http_only': False, 'max_age': 2592000}


def test_parse_set_cookie_max_age_invalid():
    with pytest.raises(ValueError):
        parse_set_cookie('cookie=123; Max-Age=foo')


def test_parse_set_cookie_domain():
    name, value, params = parse_set_cookie(
        'qwerty=219ffwef9w0f; Domain=somecompany.co.uk'
    )
    assert name == 'qwerty'
    assert value == '219ffwef9w0f'
    assert params == {
        'secure': False,
        'http_only': False,
        'domain': 'somecompany.co.uk',
    }


def test_parse_set_cookie_domain_2():
    name, value, params = parse_set_cookie(
        'sessionId=e8bb43229de9; Domain=foo.example.com'
    )
    assert name == 'sessionId'
    assert value == 'e8bb43229de9'
    assert params == {
        'secure': False,
        'http_only': False,
        'domain': 'foo.example.com',
    }


def test_parse_set_cookie_path():
    name, value, params = parse_set_cookie('cookie=123; Path=/foo/bar')
    assert name == 'cookie'
    assert value == '123'
    assert params == {'secure': False, 'http_only': False, 'path': '/foo/bar'}


def test_parse_set_cookie_path_string():
    name, value, params = parse_set_cookie('cookie=123; Path="/foo/bar"')
    assert name == 'cookie'
    assert value == '123'
    assert params == {'secure': False, 'http_only': False, 'path': '/foo/bar'}


def test_parse_set_cookie_secure():
    name, value, params = parse_set_cookie('cookie=123; Secure')
    assert name == 'cookie'
    assert value == '123'
    assert params == {'secure': True, 'http_only': False}


def test_parse_set_cookie_http_only():
    name, value, params = parse_set_cookie('cookie=123; HttpOnly')
    assert name == 'cookie'
    assert value == '123'
    assert params == {'secure': False, 'http_only': True}


def test_parse_set_cookie_same_site_lax():
    name, value, params = parse_set_cookie('cookie=123; SameSite=Lax')
    assert name == 'cookie'
    assert value == '123'
    assert params == {'secure': False, 'http_only': False, 'same_site': 'lax'}


def test_parse_set_cookie_same_site_strict():
    name, value, params = parse_set_cookie('cookie=123; SameSite=Strict')
    assert name == 'cookie'
    assert value == '123'
    assert params == {
        'secure': False,
        'http_only': False,
        'same_site': 'strict',
    }


def test_parse_set_cookie_same_site_none():
    name, value, params = parse_set_cookie('cookie=123; SameSite=None')
    assert name == 'cookie'
    assert value == '123'
    assert params == {'secure': False, 'http_only': False, 'same_site': 'none'}


def test_parse_set_cookie_same_site_invalid():
    with pytest.raises(ValueError):
        parse_set_cookie('cookie=123; SameSite=Invalid')
