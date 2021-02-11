from io import BytesIO
import os

from .http.stream import Stream
from .multidict import MultiDict


class File(Stream):

    def __init__(self, name, content_type, content):
        super().__init__(content)
        self.name = name
        self._content_type = content_type

    def _get_content_type(self):
        return self._content_type


def generate_boundary():
    return '----------------' + os.urandom(32).hex()


def parse(data, boundary):
    boundary = boundary.encode()
    start = b'--' + boundary
    end = b'--' + boundary + b'--'
    lines = iter(data.split(b'\n'))

    data = MultiDict()

    line = next(lines)  # Split always returns at least 1 result
    if line == end:
        return data
    if line != start:
        raise ValueError('invalid form data: missing boundary')

    while True:
        headers = {}
        while True:
            try:
                line = next(lines)
            except StopIteration:
                raise ValueError('invalid form data: unexpected end of data')
            if not line:
                break
            try:
                key, value = line.split(b': ', 1)
            except ValueError:
                raise ValueError('invalid form data: expected header')
            headers[key.lower()] = value

        try:
            disposition = headers.pop(b'content-disposition').split(b'; ')
        except KeyError:
            raise ValueError(
                'invalid form data: expected header Content-Disposition'
            )
        if len(disposition) < 2:
            raise ValueError(
                'invalid form data: missing data in Content-Disposition'
            )
        if len(disposition) > 3:
            raise ValueError(
                'invalid form data: unexpected data in Content-Disposition'
            )
        if disposition[0] != b'form-data':
            raise ValueError(
                'invalid form data: expected form-data Content-Disposition'
            )
        if not disposition[1].startswith(b'name='):
            raise ValueError(
                'invalid form data: expected name in Content-Disposition'
            )
        name = disposition[1][len(b'name:'):].decode()
        if len(disposition) == 3:
            if not disposition[2].startswith(b'filename='):
                raise ValueError(
                    'invalid form data: expected filename in '
                    'Content-Disposition'
                )
            file_name = disposition[2][len(b'filename='):].decode()
        else:
            file_name = None

        if file_name is None:
            content_type = None
        else:
            try:
                content_type = headers.pop(b'content-type').decode()
            except KeyError:
                raise ValueError(
                    'invalid form data: expected header Content-Type'
                )

        if headers:
            raise ValueError(
                'invalid form data: unexpected header ' +
                next(iter(headers)).decode()
            )

        value = BytesIO()
        first = True
        while True:
            try:
                line = next(lines)
            except StopIteration:
                raise ValueError('invalid form data: unexpected end of data')
            if line in [start, end]:
                break
            if first:
                first = False
            else:
                value.write(b'\n')
            value.write(line)

        value = value.getvalue()
        if file_name is not None:
            value = File(file_name, content_type, value)
        else:
            value = value.decode()
        data.appendlist(name, value)

        if line == end:
            break

    return data


async def serialize(data, boundary):
    boundary = boundary.encode()
    start = b'--' + boundary + b'\n'
    end = b'--' + boundary + b'--\n'

    if isinstance(data, MultiDict):
        items = data.allitems()
    elif hasattr(data, 'items'):
        items = data.items()
    else:
        items = iter(data)

    for name, value in items:
        yield start
        yield b'Content-Disposition: form-data; name='
        yield name.encode()
        if isinstance(value, File):
            yield b'; filename='
            yield value.name.encode()
            yield b'\nContent-Type: '
            yield value._content_type.encode()
            value = await value.body()
        else:
            value = value.encode()
        yield b'\n\n'
        yield value
        yield b'\n'
    yield end
