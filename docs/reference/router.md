This method provides a class that makes it easy to create a routed ASGI
application that uses the HTTP API of [jackie.http](http.md) for the
implementation of it's endpoints.

## `Router`
`class Router()`

A class that can be used as an ASGI application.

### Methods
#### `route`
`method route(methods, matcher, view=None, *, name=None)`

Registers a view to the router for the given methods and matcher.

`methods` must be a set of HTTP methods as uppercase strings or `'WEBSOCKET'`.
If `methods` is a `str` it will be interpreted as if it was a set with that
string as it's only item.

`matcher` must be an instance of [`Matcher`](router.md#matcher). If `matcher`
is a `str` it will be used as pattern to create a
[`Matcher`](router.md#matcher).

`view` must be a callable using the HTTP API provided by
[`jackie.http`](http.md). If view is `None` this method will return a decorator
that can be used to register such a view while leaving the original view
unmodified.

`name` is an optional `str` that can be used to reverse urls using the
[`reverse`](router.md#reverse) method.

#### `include`
`method include(matcher, router, *, name=None)`

Includes another router inside the router, the matcher here works as a prefix.
The subrouter's error handling views will be ignored.

`matcher` must be an instance of [`Matcher`](router.md#matcher). If `matcher`
is a `str` it will be used as pattern to create a
[`Matcher`](router.md#matcher).

`router` must be an instance of [`Router`](router.md#router).

`name` is an optional `str` that can be used to reverse urls using the
[`reverse`](router.md#reverse) method.

#### `not_found`
`method not_found(view)`

Registers a view to be used in case no view could be found for the provided
path.

#### `method_not_allowed`
`method method_not_allowed(view)`

Registers a view to be used in case there were views found but not for the
right method.

#### `middleware`
`method middleware(middleware)`

Registers middleware.

`middleware` is a function that takes a view and returns a view.

This wrapper will be used on every request.

#### `get`
`method get(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'GET'`.

#### `post`
`method post(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'POST'`.

#### `put`
`method put(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'PUT'`.

#### `delete`
`method delete(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'DELETE'`.

#### `connect`
`method connect(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'CONNECT'`.

#### `options`
`method options(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'OPTIONS'`.

#### `trace`
`method trace(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'TRACE'`.

#### `patch`
`method patch(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'PATCH'`.

#### `websocket`
`method websocket(matcher, view=None, *, name=None)`

A shorthand for [`route`](router.md#route) where methods is filled as `'WEBSOCKET'`.

#### `reverse`
`method reverse(name, **params)`

Reverses a url for the given `name` with the provided `params` as parameters.

`name` refers to the name used in the [`route`](router.md#route) method. For
matching a route inside a named subrouter from [`include`](router.md#include)
names must be joined with a `:`.

## Matcher
`class Matcher(pattern='')`

A helper class for matching paths and extracting parameters from them.

`pattern` is a string that looks like the path.

Parameters are delimited by `<` and `>` and should contain the name of the
parameter.

You can optionally specify the type of the parameter by adding a `:`
and the name of the type after the parameter.
Available types are `str`, `int` and `path`. Path differs from `str` in that
`/` is not allowed in `str` while it is in `path`.
If no type is provided `str` is assumed.

Some examples:
- `'/user/<id:int>/'`
- `'/file/<path:path>'`
- `'/compare/<left>/to/<right>/'`

### Methods
#### `__add__`
Matchers can be added to get one big matcher which matches the two matchers in
sequence.

#### `fullmatch`
`method fullmatch(path)`

Tries to match the path to the matcher.
In case of a match returns a `dict` containing all matched parameters.
If the path does not match this will throw a
[`Matcher.Error`](router.md#matchererror).

#### `match`
`method match(path)`

Similar to [`fullmatch`](router.md#fullmatch) but also returns succesfully if
only a prefix of the path matches instead of the entire path. Instead of a 
`dict` of params this method will return a 2-tuple consisting of the `dict` of
params and the part of `path` that was not used in the match.

#### `reverse`
`method reverse(**params)`

Returns a path that would match using the provided `params`.

## Matcher.Error
`class Matcher.Error()`

A subclass of `ValueError` that is used to indicate a failed match.
