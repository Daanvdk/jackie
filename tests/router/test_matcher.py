import pytest

from jackie.router.matcher import Matcher


def test_match_fixed():
    matcher = Matcher('foobar')

    assert matcher.fullmatch('foobar') == {}
    with pytest.raises(Matcher.Error):
        matcher.fullmatch('foo')
    with pytest.raises(Matcher.Error):
        matcher.fullmatch('foobarbaz')

    matcher.reverse()


def test_match_param():
    matcher = Matcher('foo/<key>/baz')

    assert matcher.fullmatch('foo/bar/baz') == {'key': 'bar'}
    assert matcher.fullmatch('foo/123/baz') == {'key': '123'}
    with pytest.raises(Matcher.Error):
        matcher.fullmatch('foo/baz')
    with pytest.raises(Matcher.Error):
        matcher.fullmatch('foo/bar/123/baz')

    assert matcher.reverse(key='bar') == 'foo/bar/baz'
    assert matcher.reverse(key='123') == 'foo/123/baz'
    with pytest.raises(KeyError):
        matcher.reverse()


def test_int_param():
    matcher = Matcher('foo/<key:int>/baz')

    assert matcher.fullmatch('foo/123/baz') == {'key': 123}
    with pytest.raises(Matcher.Error):
        matcher.fullmatch('foo/bar/baz')
    with pytest.raises(Matcher.Error):
        matcher.fullmatch('foo/baz')
    with pytest.raises(Matcher.Error):
        matcher.fullmatch('foo/bar/123/baz')

    assert matcher.reverse(key=123) == 'foo/123/baz'
    with pytest.raises(KeyError):
        matcher.reverse()


def test_invalid_param_type():
    with pytest.raises(ValueError):
        Matcher('foo/<key:invalid_param_type>/baz')


def test_add_matchers():
    matcher = Matcher('foo') + Matcher('bar')

    assert matcher.fullmatch('foobar') == {}
    with pytest.raises(Matcher.Error):
        assert matcher.fullmatch('foo')
    with pytest.raises(Matcher.Error):
        assert matcher.fullmatch('bar')

    with pytest.raises(TypeError):
        matcher = Matcher('foo') + 'bar'
