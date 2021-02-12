import pytest

from jackie import multipart
from jackie.multidict import MultiDict


@pytest.mark.asyncio
async def test_parse():
    body = (
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foo\n'
        b'\n'
        b'123\n'
        b'--boundary\n'
        b'Content-Disposition: form-data; name=bar\n'
        b'\n'
        b'456\n'
        b'--boundary\n'
        b'Content-Disposition: form-data; name=baz; filename=baz.txt\n'
        b'Content-Type: text/plain; charset=UTF-8\n'
        b'\n'
        b'789\n'
        b'--boundary--\n'
    )
    data = multipart.parse(body, 'boundary')
    assert set(data) == {'foo', 'bar', 'baz'}
    assert data['foo'] == '123'
    assert data['bar'] == '456'
    assert isinstance(data['baz'], multipart.File)
    assert data['baz'].name == 'baz.txt'
    assert data['baz'].content_type == 'text/plain'
    assert data['baz'].charset == 'UTF-8'
    with pytest.raises(ValueError):
        data['baz'].boundary
    assert data['baz'].content == b'789'


@pytest.mark.asyncio
async def test_parse_nested():
    body = (
        b'--outer-boundary\n'
        b'Content-Disposition: form-data; name=inner; filename=inner\n'
        b'Content-Type: multipart/form-data; boundary=inner-boundary\n'
        b'\n'
        b'--inner-boundary\n'
        b'Content-Disposition: form-data; name=foo\n'
        b'\n'
        b'bar\n'
        b'--inner-boundary--\n'
        b'--outer-boundary--\n'
    )

    data = multipart.parse(body, 'outer-boundary')
    assert set(data) == {'inner'}
    assert isinstance(data['inner'], multipart.File)
    assert data['inner'].name == 'inner'
    assert data['inner'].content_type == 'multipart/form-data'
    assert data['inner'].boundary == 'inner-boundary'

    data = multipart.parse(data['inner'].content, 'inner-boundary')
    assert set(data) == {'foo'}
    assert data['foo'] == 'bar'


def test_parse_no_start():
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(b'blaat', 'boundary')
    assert str(exc_info.value) == 'invalid form data: missing boundary'


def test_parse_no_data():
    data = multipart.parse(b'--boundary--', 'boundary')
    assert data == {}


def test_parse_unexpected_end_in_headers():
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(b'--boundary', 'boundary')
    assert str(exc_info.value) == 'invalid form data: unexpected end of data'


def test_parse_invalid_header():
    body = (
        b'--boundary\n'
        b'foobar\n'
        b'\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == 'invalid form data: expected header'


def test_parse_no_content_disposition():
    body = (
        b'--boundary\n'
        b'\n'
        b'foobar\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: expected header Content-Disposition'
    )


def test_parse_content_disposition_missing_data():
    body = (
        b'--boundary\n'
        b'Content-Disposition: form-data\n'
        b'\n'
        b'foobar\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: expected name in Content-Disposition'
    )


def test_parse_content_disposition_unexpected_data():
    body = (
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foo; foo=bar\n'
        b'\n'
        b'foobar\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: unexpected Content-Disposition param foo'
    )


def test_parse_content_disposition_wrong_value():
    body = (
        b'--boundary\n'
        b'Content-Disposition: invalid; name=foobar\n'
        b'\n'
        b'foobar\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: expected form-data Content-Disposition'
    )


def test_parse_content_disposition_no_name():
    body = (
        b'--boundary\n'
        b'Content-Disposition: form-data\n'
        b'\n'
        b'foobar\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: expected name in Content-Disposition'
    )


def test_parse_file_without_content_type():
    body = (
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foobar; filename=foobar.txt\n'
        b'\n'
        b'foobar\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: expected header Content-Type'
    )


def test_parse_unexpected_header():
    body = (
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foobar\n'
        b'Unexpected: foobar\n'
        b'\n'
        b'foobar\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: unexpected header unexpected'
    )


def test_parse_unexpected_end_of_data():
    body = (
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foobar\n'
        b'\n'
        b'foobar\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: unexpected end of data'
    )


def test_parse_invalid_content_disposition():
    body = (
        b'--boundary\n'
        b'Content-Disposition: foo; bar; baz\n'
        b'\n'
        b'foobar\n'
        b'--boundary--\n'
    )
    with pytest.raises(ValueError) as exc_info:
        multipart.parse(body, 'boundary')
    assert str(exc_info.value) == (
        'invalid form data: invalid Content-Disposition: 8: got \';\', '
        'expected \'=\''
    )


@pytest.mark.asyncio
async def test_serialize():
    data = {
        'foo': '123',
        'bar': '456',
        'baz': multipart.File('baz.txt', 'text/plain; charset=UTF-8', b'789'),
    }
    chunks = []
    async for chunk in multipart.serialize(data, 'boundary'):
        chunks.append(chunk)
    body = b''.join(chunks)
    assert body == (
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foo\n'
        b'\n'
        b'123\n'
        b'--boundary\n'
        b'Content-Disposition: form-data; name=bar\n'
        b'\n'
        b'456\n'
        b'--boundary\n'
        b'Content-Disposition: form-data; name=baz; filename=baz.txt\n'
        b'Content-Type: text/plain; charset=UTF-8\n'
        b'\n'
        b'789\n'
        b'--boundary--\n'
    )


@pytest.mark.asyncio
async def test_serialize_multidict():
    data = MultiDict([('foo', '1'), ('foo', '2')])
    chunks = []
    async for chunk in multipart.serialize(data, 'boundary'):
        chunks.append(chunk)
    body = b''.join(chunks)
    assert body == (
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foo\n'
        b'\n'
        b'1\n'
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foo\n'
        b'\n'
        b'2\n'
        b'--boundary--\n'
    )


@pytest.mark.asyncio
async def test_serialize_items():
    data = [('foo', '1'), ('foo', '2')]
    chunks = []
    async for chunk in multipart.serialize(data, 'boundary'):
        chunks.append(chunk)
    body = b''.join(chunks)
    assert body == (
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foo\n'
        b'\n'
        b'1\n'
        b'--boundary\n'
        b'Content-Disposition: form-data; name=foo\n'
        b'\n'
        b'2\n'
        b'--boundary--\n'
    )
