import pytest

from jackie.multidict import MultiDict, Headers


def test_get():
    multidict = MultiDict(foo=1, bar=2)

    assert multidict['foo'] == 1
    assert multidict['bar'] == 2
    with pytest.raises(KeyError):
        multidict['baz']

    multidict = MultiDict({'foo': 1, 'bar': 2})

    assert multidict['foo'] == 1
    assert multidict['bar'] == 2
    with pytest.raises(KeyError):
        multidict['baz']

    multidict = MultiDict([('foo', 'double!'), ('foo', 1), ('bar', 2)])

    assert multidict['foo'] == 1
    assert multidict['bar'] == 2
    with pytest.raises(KeyError):
        multidict['baz']

    assert multidict.getlist('foo') == ['double!', 1]
    assert multidict.getlist('bar') == [2]
    assert multidict.getlist('baz') == []

    multidict = MultiDict(multidict)

    assert multidict['foo'] == 1
    assert multidict['bar'] == 2
    with pytest.raises(KeyError):
        multidict['baz']

    assert multidict.getlist('foo') == ['double!', 1]
    assert multidict.getlist('bar') == [2]
    assert multidict.getlist('baz') == []


def test_del():
    multidict = MultiDict([('foo', 1), ('foo', 2)])
    assert multidict['foo'] == 2
    del multidict['foo']
    with pytest.raises(KeyError):
        multidict['foo']
    with pytest.raises(KeyError):
        del multidict['foo']


def test_len():
    multidict = MultiDict([('foo', 1), ('bar', 2), ('baz', 3), ('foo', 4)])
    assert len(multidict) == 3


def test_iter():
    multidict = MultiDict([('foo', 1), ('bar', 2), ('baz', 3), ('foo', 4)])
    assert set(multidict) == {'foo', 'bar', 'baz'}


def test_setlist():
    multidict = MultiDict([('foo', 1), ('foo', 2)])
    assert multidict.getlist('foo') == [1, 2]
    multidict.setlist('foo', [3, 4])
    assert multidict.getlist('foo') == [3, 4]
    multidict.setlist('foo', [])
    with pytest.raises(KeyError):
        multidict['foo']


def test_appendlist():
    multidict = MultiDict([('foo', 1)])
    assert multidict.getlist('foo') == [1]
    multidict.appendlist('foo', 2)
    assert multidict.getlist('foo') == [1, 2]


def test_extendlist():
    multidict = MultiDict([('foo', 1)])
    assert multidict.getlist('foo') == [1]
    multidict.extendlist('foo', [2, 3])
    assert multidict.getlist('foo') == [1, 2, 3]
    multidict.extendlist('bar', [])
    with pytest.raises(KeyError):
        multidict['bar']


def test_poplist():
    multidict = MultiDict([('foo', 1), ('foo', 2), ('foo', 3)])
    assert multidict.poplist('foo') == 3
    assert multidict.poplist('foo') == 2
    assert multidict.poplist('foo') == 1
    with pytest.raises(KeyError):
        multidict['foo']


def test_headers():
    headers = Headers()
    headers['Content-Type'] = b'text/plain'
    assert headers['cOnTenT-TYPe'] == 'text/plain'
    with pytest.raises(TypeError):
        headers[1] = 'foo'
    with pytest.raises(TypeError):
        headers['foo'] = 1
