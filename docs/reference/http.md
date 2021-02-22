This module provides the building blocks to work with HTTP in jackie.

## `Request`
`class Request(path='/', *, form, method='GET', query=[], headers=[], **headers)`
`class Request(path='/', *, json, method='GET', query=[], headers=[], **headers)`
`class Request(path='/', *, text, method='GET', query=[], headers=[], **headers)`
`class Request(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Represents a request from a client to the application.

Both `query` and `headers` expect a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

There are 4 parameters that can describe the body of the request. `form`,
`json`, `text` or `body`. At most one of these can be supplied.

`form` must be a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict) where the keys are strings and the values
are either strings or a [`File`](multipart.md#file).

`json` must be data that is JSON-encodable.

`text` must be a str.

`body` must be `bytes`, an iterable of `bytes` or an async iterable of `bytes`.

If none of these 4 parameters is supplied `body` defaults to `b''`.

This class implements [`Stream`](http.md#stream).

### Attributes
#### `method`
A string representing the HTTP request method of the request. This is always in
uppercase.

#### `path`
A string representing the path that was requested.

#### `headers`
A [`Headers`](multidict.md#headers) object containing all request headers.

#### `cookies`
A dict mapping `str` to `str` containing the cookies sent by the client.

## `Response`
`class Response(*, form, status=200, content_type=None, set_cookies=[], headers=[], **headers)`  
`class Response(*, json, status=200, content_type=None, set_cookies=[], headers=[], **headers)`  
`class Response(*, text, status=200, content_type=None, set_cookies=[], headers=[], **headers)`  
`class Response(*, html, status=200, content_type=None, set_cookies=[], headers=[], **headers)`  
`class Response(*, redirect, status=304, content_type=None, set_cookies=[], headers=[], **headers)`  
`class Response(*, body=b'', status=200, content_type=NoneNone, set_cookies=[], headers=[], **headers)`

Represents a response from the application to a client.

Both `query` and `headers` expect a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

`content_type` sets the `Content-Type` header.

There are 6 parameters that can describe the body of the response. `form`,
`json`, `text`, `html`, `redirect` or `body`. At most one of these can be supplied.

`form` must be a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict) where the keys are strings and the values
are either strings or a [`File`](multipart.md#file).

`json` must be data that is JSON-encodable.

`text` must be a str.

`html` must be a str containing an HTML document.

`redirect` must be a str with the location to redirect to. Note that when
`redirect` is provided the default `status` is `304` instead of `200`.

`body` must be `bytes`, an iterable of `bytes` or an async iterable of `bytes`.

If none of these 6 parameters is supplied `body` defaults to `b''`.

`set_cookies` expects an iterable of [`Cookie`](http.md#cookie) that will be
added as `Set-Cookie` response headers.

This class implements [`Stream`](http.md#stream).

### Attributes
#### `status`
An integer representing the HTTP status code of the response.

#### `headers`
A [`Headers`](multidict.md#headers) object containing all response headers.

#### `ok`
A boolean indicating whether the response is considered 'ok' according to the
HTTP status code. This is implemented as `status < 400`.

## `Stream`
`class Stream(chunks=b'')`

This is an abstract base class that represents something with a stream of
binary data and a content type. It is mainly used as base class for both
[`Request`](http.md#request) and [`Response`](http.md#response).

### Attributes
#### `content_type`
The basic content type without any metadata like the charset.

#### `charset`
The charset of the content.

#### `boundary`
The boundary of the content. This is mostly relevant for `multipart` content
types.

### Methods
#### `chunks`
`method chunks()`
Returns an async iterator of chunks of data. These chunks will be of type
`bytes`.

#### `body`
`coroutine body()`
Returns the contents of the stream as `bytes`.

#### `text`
Returns the contents of the stream as a string.

#### `json`
Returns the contents of the stream parsed as json.

#### `form`
Returns the contents of the stream parsed as form data.
How the stream is parsed is dependent on the `content_type`, both
`application/x-www-form-urlencoded` and `multipart/form-data` are supported.

## `Socket`
`class Socket(path='/', *, accept, close, receive, send, query=[], headers=[], **headers)`

Represents a websocket connection from a client to the application.

Both `query` and `headers` expect a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

`accept`, `close`, `receive`, and `send` should be coroutines that respectively
accept the connection, close the connection, receive a message from the socket
or send a message to the socket.

### Attributes
#### `method`
This will always be equal to `'websocket'`. This attribute is present to easily
differentiate between [`Socket`](http.md#socket)s and
[`Request`](http.md#request)s.

#### `path`
A string representing the path that was requested.

#### `headers`
A [`Headers`](multidict.md#headers) object containing all request headers.

#### `cookies`
A dict mapping `str` to `str` containing the cookies sent by the client.

### Methods
#### `accept`
`coroutine accept(headers=[], set_cookies=[], **headers)`

Accepts the connection with the provided response headers.

`headers` expects a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

`set_cookies` expects an iterable of [`Cookie`](http.md#cookie) that will be
added as `Set-Cookie` response headers.

#### `close`
`coroutine close(code=1000)`

Closes the connection with the provided `code`.

#### `receive_bytes`
`coroutine receive_bytes()`

Receive a message from the socket as `bytes`.

#### `receive_text`
`coroutine receive_text()`

Receive a message from the socket as `str`.

#### `receive_json`
`coroutine receive_bytes()`

Receive a message from the socket as parsed json.

#### `send_bytes`
`coroutine send_bytes(data)`

Sends data over the socket.

`data` must be `bytes`.

#### `send_text`
`coroutine send_bytes(data)`

Sends data over the socket.

`data` must be `str`.

#### `send_json`
`coroutine send_bytes(data)`

Sends data over the socket as JSON.

`data` must be JSON encodable.

## `Cookie`
`Cookie(name, value, *, expires=None, max_age=None, domain=None, path=None, secure=False, http_only=False, same_site=None)`

Represents a cookie that can be set.

`expires` must be a timezone aware datetime or `None`.

`max_age` must be an integer or `None`.

`domain` must be a str or `None`.

`path` must be a str or `None`.

`same_site` must be one of `'lax'`, `'strict'`, `'none'` or `None`.

### Attributes
#### `expires`
A `datetime` indicating when the cookie will expire.
Can also equal `None` in which case the cookie will expire at the end of the
session.

#### `max_age`
An `int` indicating when the cookie will expire. The cookie will expire
`max_age` seconds after receival.
Can also equal `None` in which case the cookie will expire at the end of the
session.

#### `domain`
The domain for which the cookie should be set as a `str`.
Can also equal `None` in which case the current domain will be used.

#### `path`
The path for which the cookie should be set.
Can also equal `None` in which case the root will be used.

#### `same_site`
A value indicating when to send the cookie. There are 3 options:

- `strict`, which means the cookie will only be sent on requests originating
from the domain/path the cookie belongs to itself.
- `lax`, which is similar to `strict` but also includes the cookie when a user
navigates to the domain/path.
- `none`, which does no checking on the origin of the request.

Can also equal `None` in which case the cookie will behave as `lax`. On older
clients the behaviour of `none` will be used instead when no value is present.

### Methods
#### `encode`
`method encode()`

Returns a `str` of the cookie encoded as the value of `Set-Cookie`-header.

## `Disconnect`
`class Disconnect(code=None)`

An exception that represents an HTTP Disconnect.

### Attributes
#### `code`
The websocket close code in a websocket context, otherwise `None`.

## `asgi_to_jackie`
`asgi_to_jackie(app)`

Converts an ASGI application `app` into a jackie view.

If `app` was created by [`jackie_to_asgi`](#jackie_to_asgi) it will return the
original view instead.

## `jackie_to_asgi`
`asgi_to_jackie(view)`

Converts a jackie view `view` into an ASGI application.

If `view` was created by [`asgi_to_jackie`](#asgi_to_jackie) it will return the
original application instead.
