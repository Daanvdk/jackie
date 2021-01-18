import pytest

from jack.multidict import MultiDict


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
