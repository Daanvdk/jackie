from ..serialize import serialize_set_cookie


class Cookie:

    def __init__(
        self, name, value, *, expires=None, max_age=None, domain=None,
        path=None, secure=False, http_only=False, same_site=None,
    ):
        self.name = name
        self.value = value
        self.expires = expires
        self.max_age = max_age
        self.domain = domain
        self.path = path
        self.secure = bool(secure)
        self.http_only = bool(http_only)
        self.same_site = same_site

    def serialize(self):
        params = {}
        for attr in [
            'expires', 'max_age', 'domain', 'path', 'secure', 'http_only',
            'same_site',
        ]:
            value = getattr(self, attr)
            if value is not None:
                params[attr] = value
        return serialize_set_cookie(self.name, self.value, params)
