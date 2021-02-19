This module provides Mappings that allow multiple values per key which is a
common pattern in HTTP. (headers, query parameters, form data, etc.)

## `MultiDict`
`class MultiDict(items=[], **items)`

A class that can be used as a mapping of keys to multiple values.

The initial items can be supplied by an iterator of 2-tuples and/or keyword
arguments.

### Methods
All methods from [`collections.abc.MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)
are provided. Since these methods are all based on Mappings where keys have 1
value they when setting overwrite all values to the one value and when getting
get the last value.

#### `getlist`
`method getlist(key)`

Gets all values for a key. Returns a list.

#### `setlist`
`method setlist(key, values)`

Sets all values for a key.

`values` must be an iterable.

#### `appendlist`
`method appendlist(key, value)`

Append a value to the existing values for a key.

#### `extendlist`
`method extendlist(key, values)`

Extends the existing values for a key.

`values` must be an iterable.

#### `poplist`
`method poplist(key)`

Pops the last value from the values for a key.

#### `allitems`
`method allitems()`

Returns an iterable of 2-tuples for all key value combinations.

This differes from the standard `items` in that when a key has multiple values
they will all appear in the iterable while the standard `items` would only
include the last value.

## `Headers`
`class Headers(items=[], **items)`

A subclass of [`MultiDict`](multidict.md#multidict) that does some conversions
on keys and values to have behaviour consistent with HTTP headers.

Both keys and values should be of type `str`. `bytes` is automatically
converted, other types will error.

Keys are lowercased to ensure case insensitive behaviour.
