import re


WORD_PATTERN = r'[A-Za-z_][A-Za-z0-9_]*'
PARAM_PATTERN = fr'<\s*({WORD_PATTERN})\s*(?::\s*({WORD_PATTERN})\s*)?>'
PARAM_RE = re.compile(PARAM_PATTERN)


# mapping of name -> 3 tuple consisting of:
#   - a pattern to match the param
#   - a parser to parse the param to a value
#   - a serializer to serialize a value back to a param
PARAM_TYPES = {
    'str': (r'[^//]+', str, str),
    'int': (r'\d+', int, str),
    'path': (r'.+', str, str),
}


class Matcher:

    def __init__(self, pattern=''):
        parts = []
        params = []

        index = 0

        for match in PARAM_RE.finditer(pattern):
            if index != match.start():
                parts.append(re.escape(pattern[index:match.start()]))

            name, param_type = match.groups()
            if param_type is None:
                param_type = 'str'
            try:
                param_pattern, _, _ = PARAM_TYPES[param_type]
            except KeyError:
                raise ValueError(f'invalid param type: {param_type}') from None
            parts.append(f'({param_pattern})')
            params.append((name, param_type))

            index = match.end()

        if index != len(pattern):
            parts.append(re.escape(pattern[index:]))

        self.regex = re.compile(r''.join(parts))
        self.params = params

    def __add__(self, other):
        if not isinstance(other, Matcher):
            raise TypeError
        merged = Matcher()
        merged.regex = re.compile(self.regex.pattern + other.regex.pattern)
        merged.params = [*self.params, *other.params]
        return merged

    def match(self, path):
        match = self.regex.match(path)
        if match is None:
            raise self.Error
        params = {}
        for (name, param_type), value in zip(self.params, match.groups()):
            _, parse, _ = PARAM_TYPES[param_type]
            params[name] = parse(value)
        return params, path[match.end():]

    def fullmatch(self, path):
        params, path = self.match(path)
        if path:
            raise self.Error
        return params

    def reverse(self, **params):
        parts = []

        chars = iter(self.regex.pattern)
        param_index = 0
        depth = 0

        for char in chars:
            if char == '(':
                depth += 1
            elif char == ')':
                assert depth > 0
                depth -= 1
                if depth == 0:
                    name, param_type = self.params[param_index]
                    _, _, serialize = PARAM_TYPES[param_type]
                    parts.append(serialize(params[name]))
                    param_index += 1
                    continue
            elif char == '\\':
                char = next(chars)
            if depth == 0:
                parts.append(char)

        return ''.join(parts)

    class Error(ValueError):
        pass
