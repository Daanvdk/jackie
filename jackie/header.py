import functools


SPACE = ' \t'
CONTROL = '()<>@,;:\\/[]?={}'


def lex_header(content):
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
            content = list(lex_header(content)), 0
            content, result = parse(content, *args, **kwargs)
            parse_token(content, 'end')
            return result
        else:
            return parse(content, *args, **kwargs)
    return wrapped_parse


@parser
def parse_token(content, *keys, optional=False):
    tokens, index = content
    key, i, _ = tokens[index]
    if key in keys:
        return (tokens, index + 1), tokens[index]
    if optional:
        return content, None
    keys = list(map(repr, sorted(keys)))
    if len(keys) == 1:
        keys = keys[0]
    else:
        keys = ', '.join(keys[:-1]) + ' or ' + keys[-1]
    raise ValueError(f'{i}: got {key!r}, expected {keys}')


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
