import pytest

from jackie.router.matcher import Matcher


def test_match_fixed():
    matcher = Matcher('foobar')

    assert matcher.match('foobar') == {}
    with pytest.raises(Matcher.Error):
        matcher.match('foo')
    with pytest.raises(Matcher.Error):
        matcher.match('foobarbaz')

    matcher.reverse()


def test_match_param():
    matcher = Matcher('foo/<key>/baz')

    assert matcher.match('foo/bar/baz') == {'key': 'bar'}
    assert matcher.match('foo/123/baz') == {'key': '123'}
    with pytest.raises(Matcher.Error):
        matcher.match('foo/baz')
    with pytest.raises(Matcher.Error):
        matcher.match('foo/bar/123/baz')

    assert matcher.reverse(key='bar') == 'foo/bar/baz'
    assert matcher.reverse(key='123') == 'foo/123/baz'
    with pytest.raises(KeyError):
        matcher.reverse()


def test_int_param():
    matcher = Matcher('foo/<key:int>/baz')

    assert matcher.match('foo/123/baz') == {'key': 123}
    with pytest.raises(Matcher.Error):
        matcher.match('foo/bar/baz')
    with pytest.raises(Matcher.Error):
        matcher.match('foo/baz')
    with pytest.raises(Matcher.Error):
        matcher.match('foo/bar/123/baz')

    assert matcher.reverse(key=123) == 'foo/123/baz'
    with pytest.raises(KeyError):
        matcher.reverse()


def test_invalid_param_type():
    with pytest.raises(ValueError):
        Matcher('foo/<key:invalid_param_type>/baz')


def test_add_matchers():
    matcher = Matcher('foo') + Matcher('bar')

    assert matcher.match('foobar') == {}
    with pytest.raises(Matcher.Error):
        assert matcher.match('foo')
    with pytest.raises(Matcher.Error):
        assert matcher.match('bar')

    with pytest.raises(TypeError):
        matcher = Matcher('foo') + 'bar'
