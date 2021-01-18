from collections.abc import MutableMapping
from itertools import chain


class MultiDict(MutableMapping):

    def __init__(self, items=[], **kwargs):
        if isinstance(items, MultiDict):
            items = items.allitems()
        elif isinstance(items, dict):
            items = items.items()
        if kwargs:
            items = chain(items, kwargs.items())
        values = {}
        for key, value in items:
            key = self._clean_key(key)
            value = self._clean_value(value)
            values.setdefault(key, []).append(value)
        self._values = values

    def __getitem__(self, key):
        key = self._clean_key(key)
        return self._values[key][-1]

    def __setitem__(self, key, value):
        key = self._clean_key(key)
        value = self._clean_value(value)
        self._values[key] = [value]

    def __delitem__(self, key):
        key = self._clean_key(key)
        del self._values[key]

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    def getlist(self, key):
        key = self._clean_key(key)
        try:
            values = self._values[key]
        except KeyError:
            return []
        else:
            return list(values)

    def setlist(self, key, values):
        key = self._clean_key(key)
        values = list(map(self._clean_value, values))
        if values:
            self._values[key] = values
        else:
            self._values.pop(key, None)

    def appendlist(self, key, value):
        key = self._clean_key(key)
        value = self._clean_value(value)
        self._values.setdefault(key, []).append(value)

    def extendlist(self, key, values):
        key = self._clean_key(key)
        values = list(map(self._clean_value, values))
        if values:
            self._values.setdefault(key, []).extend(values)

    def poplist(self, key):
        key = self._clean_key(key)
        values = self._values[key]
        value = values.pop()
        if not values:
            del self._values[key]
        return value

    def allitems(self):
        for key, values in self._values.items():
            for value in values:
                yield key, value

    def _clean_key(self, key):
        return key

    def _clean_value(self, value):
        return value


class Headers(MultiDict):

    def _clean_key(self, key):
        if isinstance(key, bytes):
            key = key.decode()
        if not isinstance(key, str):
            raise TypeError(
                'Headers key must be either str or bytes, not '
                f'{key.__class__.__name__}'
            )
        return key.lower()

    def _clean_value(self, key):
        if isinstance(key, bytes):
            key = key.decode()
        if not isinstance(key, str):
            raise TypeError(
                'Headers value must be either str or bytes, not '
                f'{key.__class__.__name__}'
            )
        return key
