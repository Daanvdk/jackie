from .parse import SPACE, CONTROL


DISALLOW = set(SPACE + CONTROL + '"')


def serialize_value(value, allow=''):
    disallow = DISALLOW - set(allow)

    if value and not any(char in disallow for char in value):
        return value

    raw_chars = iter(value)
    str_chars = ['"']
    for char in raw_chars:
        if char in '\\"':
            str_chars.append('\\')
        str_chars.append(char)
    str_chars.append('"')
    return ''.join(str_chars)


WEEKDAYS = {
    0: 'Mon',
    1: 'Tue',
    2: 'Wed',
    3: 'Thu',
    4: 'Fri',
    5: 'Sat',
    6: 'Sun',
}
MONTHS = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dec',
}


def serialize_date(date):
    parts = []
    parts.append(WEEKDAYS[date.weekday()])
    parts.append(', ')
    parts.append(str(date.day))
    parts.append(' ')
    parts.append(MONTHS[date.month])
    parts.append(' ')
    parts.append(str(date.year))
    parts.append(' ')
    parts.append(format(date.hour, '0>2'))
    parts.append(':')
    parts.append(format(date.minute, '0>2'))
    parts.append(':')
    parts.append(format(date.second, '0>2'))
    parts.append(' GMT')
    return ''.join(parts)


def serialize_set_cookie(name, value, params):
    parts = []
    parts.append(name)
    parts.append('=')
    parts.append(serialize_value(value))

    if 'expires' in params:
        parts.append('; Expires=')
        parts.append(serialize_date(params['expires']))
    if 'max_age' in params:
        parts.append('; Max-Age=')
        parts.append(str(params['max_age']))
    if 'domain' in params:
        parts.append('; Domain=')
        parts.append(serialize_value(params['domain']))
    if 'path' in params:
        parts.append('; Path=')
        parts.append(serialize_value(params['path'], '/'))
    if params['secure']:
        parts.append('; Secure')
    if params['http_only']:
        parts.append('; HttpOnly')
    if 'same_site' in params:
        parts.append('; SameSite=')
        parts.append(params['same_site'].capitalize())

    return ''.join(parts)


def serialize_cookies(cookies):
    parts = []
    for name, value in cookies.items():
        if parts:
            parts.append('; ')
        parts.append(name)
        parts.append('=')
        parts.append(serialize_value(value))
    return ''.join(parts)
