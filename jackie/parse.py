from datetime import datetime, timezone
import functools


SPACE = ' \t'
CONTROL = '()<>@,;:\\/[]?={}'


def lex(content):
    if isinstance(content, bytes):
        content = content.decode()

    index = 0

    while index < len(content):
        if content[index] in SPACE:
            index += 1

        elif content[index] == '"':
            key = 'string'
            start = index
            index += 1
            while True:
                if index >= len(content):
                    key = 'unterminated_string'
                    index = len(content)
                    break
                char = content[index]
                index += 1
                if char == '"':
                    break
                elif char == '\\':
                    index += 1
            yield (key, index, content[start:index])

        elif content[index] in CONTROL:
            yield (content[index], index, content[index])
            index += 1

        else:
            start = index
            index += 1
            while (
                index < len(content) and
                content[index] not in SPACE and
                content[index] != '"' and
                content[index] not in CONTROL
            ):
                index += 1
            yield ('name', start, content[start:index])

    yield ('end', index, b'')


def parser(parse):
    @functools.wraps(parse)
    def wrapped_parse(content, *args, **kwargs):
        if isinstance(content, (str, bytes)):
            content = list(lex(content)), 0, set()
            content, result = parse(content, *args, **kwargs)
            parse_token(content, 'end')
            return result
        else:
            return parse(content, *args, **kwargs)
    return wrapped_parse


@parser
def parse_token(content, *keys, optional=False):
    tokens, index, checked = content
    key, i, _ = tokens[index]
    if key in keys:
        return (tokens, index + 1, set()), tokens[index]
    checked = checked | set(keys)
    if optional:
        return (tokens, index, checked), None
    keys = list(map(repr, sorted(checked)))
    if len(keys) == 1:
        keys = keys[0]
    else:
        keys = ', '.join(keys[:-1]) + ' or ' + keys[-1]
    raise ValueError(f'{i}: got {key!r}, expected {keys}')


@parser
def parse_int(content):
    index = content[1]
    content, name = parse_name(content)
    try:
        return content, int(name)
    except ValueError:
        raise ValueError(f'{index}: expected an int') from None


def normalize_enum(value):
    return value.lower().replace('-', '').replace('_', '')


@parser
def parse_enum(content, *values):
    index = content[1]
    content, name = parse_name(content)
    name = normalize_enum(name)
    values = {normalize_enum(value): value for value in values}
    try:
        return content, values[name]
    except KeyError:
        raise ValueError(f'{index}: unexpected value: {name!r}') from None


WEEKDAYS = {
    'mon': 0,
    'tue': 1,
    'wed': 2,
    'thu': 3,
    'fri': 4,
    'sat': 5,
    'sun': 6,
}
MONTHS = {
    'jan': 1,
    'feb': 2,
    'mar': 3,
    'apr': 4,
    'may': 5,
    'jun': 6,
    'jul': 7,
    'aug': 8,
    'sep': 9,
    'oct': 10,
    'nov': 11,
    'dec': 12,
}


@parser
def parse_date(content):
    index = content[1]

    content, weekday = parse_enum(content, *WEEKDAYS)
    weekday = WEEKDAYS[weekday]
    content, _ = parse_token(content, ',')
    content, day = parse_int(content)
    content, month = parse_enum(content, *MONTHS)
    month = MONTHS[month]
    content, year = parse_int(content)
    content, hour = parse_int(content)
    content, _ = parse_token(content, ':')
    content, minute = parse_int(content)
    content, _ = parse_token(content, ':')
    content, second = parse_int(content)
    content, _ = parse_enum(content, 'GMT', 'UTC')

    try:
        date = datetime(
            year, month, day, hour, minute, second, tzinfo=timezone.utc,
        )
        assert date.weekday() == weekday
    except (ValueError, AssertionError):
        raise ValueError(f'{index}: invalid date') from None

    return content, date


@parser
def parse_path(content):
    _, token = parse_token(content, 'string', optional=True)
    if token:
        return parse_value(content)
    parts = []
    while True:
        content, token = parse_token(content, 'name', '/', optional=True)
        if token is None:
            break
        parts.append(token[2])
    return content, ''.join(parts)


@parser
def parse_name(content):
    content, (_, _, name) = parse_token(content, 'name')
    return content, name


@parser
def parse_value(content):
    content, (key, _, value) = parse_token(content, 'name', 'string')
    if key == 'string':
        raw_chars = iter(value[1:-1])
        str_chars = []
        for char in raw_chars:
            if char == '\\':
                char = next(raw_chars)
            str_chars.append(char)
        value = ''.join(str_chars)
    return content, value


@parser
def parse_params(content):
    params = {}
    content, more_params = parse_token(content, ';', optional=True)
    while more_params:
        content, param_key = parse_name(content)
        content, _ = parse_token(content, '=')
        content, param_value = parse_value(content)
        params[param_key] = param_value
        content, more_params = parse_token(content, ';', optional=True)
    return content, params


@parser
def parse_content_disposition(content):
    content, value = parse_value(content)
    content, params = parse_params(content)
    return content, (value, params)


@parser
def parse_media_type(content):
    content, type_ = parse_value(content)
    content, _ = parse_token(content, '/')
    content, subtype = parse_value(content)
    return content, f'{type_}/{subtype}'


@parser
def parse_content_type(content):
    if content is None:
        return None, {}
    content, media_type = parse_media_type(content)
    content, params = parse_params(content)
    return content, (media_type, params)


@parser
def parse_cookies(content):
    cookies = {}
    while True:
        _, token = parse_token(content, 'end', optional=True)
        if token is not None:
            break
        content, name = parse_name(content)
        content, _ = parse_token(content, '=')
        content, value = parse_value(content)
        cookies[name] = value
        content, token = parse_token(content, ';', optional=True)
        if token is None:
            break
    return content, cookies


@parser
def parse_set_cookie(content):
    content, cookie_name = parse_name(content)
    content, _ = parse_token(content, '=')
    content, cookie_value = parse_value(content)

    params = {'secure': False, 'http_only': False}
    content, more_params = parse_token(content, ';', optional=True)
    while more_params:
        content, param_name = parse_enum(
            content, 'expires', 'max_age', 'domain', 'path', 'secure',
            'http_only', 'same_site'
        )
        if param_name == 'expires':
            content, _ = parse_token(content, '=')
            content, param_value = parse_date(content)
        elif param_name == 'max_age':
            content, _ = parse_token(content, '=')
            content, param_value = parse_int(content)
        elif param_name == 'domain':
            content, _ = parse_token(content, '=')
            content, param_value = parse_value(content)
        elif param_name == 'path':
            content, _ = parse_token(content, '=')
            content, param_value = parse_path(content)
        elif param_name == 'secure':
            param_value = True
        elif param_name == 'http_only':
            param_value = True
        elif param_name == 'same_site':
            content, _ = parse_token(content, '=')
            content, param_value = parse_enum(content, 'lax', 'strict', 'none')
        params[param_name] = param_value
        content, more_params = parse_token(content, ';', optional=True)

    return content, (cookie_name, cookie_value, params)
