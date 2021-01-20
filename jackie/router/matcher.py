import re


WORD_PATTERN = r'[A-Za-z_][A-Za-z0-9_]*'
PARAM_PATTERN = fr'<\s*({WORD_PATTERN})\s*(?::\s*({WORD_PATTERN})\s*)?>'
PARAM_RE = re.compile(PARAM_PATTERN)


# mapping of name -> 3 tuple consisting of:
#   - a regex to match the param
#   - a parser to parse the param to a value
#   - a serializer to serialize a value back to a param
PARAM_TYPES = {
    'str': (re.compile(r'[^//]+'), str, str),
    'int': (re.compile(r'\d+'), int, str),
    'path': (re.compile(r'.+'), str, str),
}


class Matcher:

    def __init__(self, pattern=''):
        if isinstance(pattern, str):
            parts = []
            index = 0
            for match in PARAM_RE.finditer(pattern):
                if index != match.start():
                    parts.append(('str', pattern[index:match.start()]))
                name, param_type = match.groups()
                if param_type is None:
                    param_type = 'str'
                if param_type not in PARAM_TYPES:
                    raise ValueError(f'invalid param type: {param_type}')
                parts.append(('param', name, param_type))
                index = match.end()
            if index != len(pattern):
                parts.append(('str', pattern[index:]))
        else:
            parts = pattern
        self.parts = parts

    def __add__(self, other):
        if not isinstance(other, Matcher):
            raise TypeError
        left = list(self.parts)
        right = other.parts
        if left and left[-1][0] == 'str' and right and right[0][0] == 'str':
            right = iter(right)
            left[-1] = ('str', left[-1][1] + next(right)[1])
        left.extend(right)
        return Matcher(left)

    def match(self, path):
        params = {}
        index = 0

        for part in self.parts:
            if part[0] == 'str':
                _, content = part
                if not path.startswith(content, index):
                    raise self.Error(f'{index}: expected {content!r}')
                index += len(content)

            elif part[0] == 'param':
                _, name, param_type = part
                param_re, parse, serialize = PARAM_TYPES[param_type]
                match = param_re.match(path, index)
                if not match:
                    raise self.Error(f'{index}: expected {param_type}')
                params[name] = parse(match.group())
                index = match.end()

            else:  # pragma: no cover
                raise ValueError(f'invalid part: {part[0]}')

        if index != len(path):
            raise self.Error(f'{index}: expected end of path')

        return params

    def reverse(self, **params):
        parts = []

        for part in self.parts:
            if part[0] == 'str':
                _, content = part
                parts.append(content)

            elif part[0] == 'param':
                _, name, param_type = part
                param_re, parse, serialize = PARAM_TYPES[param_type]
                parts.append(serialize(params[name]))

            else:  # pragma: no cover
                raise ValueError(f'invalid part: {part[0]}')

        return ''.join(parts)

    class Error(ValueError):
        pass
