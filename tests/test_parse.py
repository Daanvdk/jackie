import pytest

from jackie.parse import parse_content_disposition, parse_content_type


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
