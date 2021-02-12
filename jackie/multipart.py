from collections import namedtuple
from io import BytesIO
import os

from .multidict import MultiDict
from .header import parse_content_disposition, parse_content_type


File = namedtuple('File', ['name', 'content_type', 'content'])


class File:

    def __init__(self, name, content_type, content):
        self.name = name
        self._content_type = content_type
        self.content = content

    @property
    def content_type(self):
        content_type, _ = parse_content_type(self._content_type)
        return content_type

    @property
    def charset(self):
        _, params = parse_content_type(self._content_type)
        return params.get('charset', 'UTF-8')

    @property
    def boundary(self):
        _, params = parse_content_type(self._content_type)
        try:
            return params['boundary']
        except KeyError:
            raise ValueError('no boundary provided') from None


def generate_boundary():
    return '----------------' + os.urandom(32).hex()


def parse(data, boundary):
    boundary = boundary.encode()
    start = b'--' + boundary
    end = b'--' + boundary + b'--'
    lines = iter(data.splitlines(True))

    data = MultiDict()

    line = next(lines).rstrip(b'\r\n')
    if line == end:
        return data
    if line != start:
        raise ValueError('invalid form data: missing boundary')

    while True:
        headers = {}
        while True:
            try:
                line = next(lines).rstrip(b'\r\n')
            except StopIteration:
                raise ValueError('invalid form data: unexpected end of data')
            if not line:
                break
            try:
                key, value = line.split(b':', 1)
            except ValueError:
                raise ValueError('invalid form data: expected header')
            headers[key.strip().lower()] = value.strip()

        try:
            disposition, disposition_params = parse_content_disposition(
                headers.pop(b'content-disposition')
            )
        except KeyError:
            raise ValueError(
                'invalid form data: expected header Content-Disposition'
            )
        except ValueError as e:
            raise ValueError(
                f'invalid form data: invalid Content-Disposition: {e}'
            ) from None

        if disposition != 'form-data':
            raise ValueError(
                'invalid form data: expected form-data Content-Disposition'
            )

        try:
            name = disposition_params.pop('name')
        except KeyError:
            raise ValueError(
                'invalid form data: expected name in Content-Disposition'
            )

        try:
            file_name = disposition_params.pop('filename')
        except KeyError:
            file_name = None

        if disposition_params:
            raise ValueError(
                'invalid form data: unexpected Content-Disposition param ' +
                next(iter(disposition_params))
            )

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
        line_end = b''
        while True:
            try:
                line = next(lines)
            except StopIteration:
                raise ValueError('invalid form data: unexpected end of data')
            stripped_line = line.rstrip(b'\r\n')
            if stripped_line in [start, end]:
                break
            value.write(line_end)
            value.write(stripped_line)
            line_end = line[len(stripped_line):]

        value = value.getvalue()
        if file_name is not None:
            value = File(file_name, content_type, value)
        else:
            value = value.decode()
        print('FIELD', name, value)
        data.appendlist(name, value)

        if stripped_line == end:
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
            value = value.content
        else:
            value = value.encode()
        yield b'\n\n'
        yield value
        yield b'\n'
    yield end
