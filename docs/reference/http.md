This module provides the building blocks to work with HTTP in jackie.

## `Request`
`class Request(path='/', *, method='GET', body=b'', query=[], headers=[], **headers)`

Represents a request from a client to the application.

Both `query` and `headers` expect a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

`body` can be `bytes`, an iterable of `bytes` or an async iterable of `bytes`.

This class implements [`Stream`](http.md#stream).

### Attributes
#### `method`
A string representing the HTTP request method of the request. This is always in
uppercase.

#### `path`
A string representing the path that was requested.

#### `headers`
A [`Headers`](multidict.md#headers) object containing all request headers.

## `FormRequest`
`class FormRequest(path='/', body={}, boundary=None, *, method='GET', query=[], headers=[], **headers)`

A subclass of [`Request`](http.md#request) that encodes the provided body as
`multipart/form-data` and sets the appropriate headers.

Body must be a `dict`, an iterable of 2-tuples or a 
[`MultiDict`](multidict.md#multidict) where the keys are strings and the values
are either strings or a [`File`](multipart.md#file).

If no `boundary` is supplied a `boundary` is automatically generated.

## `JsonRequest`
`class JsonRequest(path='/', body={}, *, method='GET', query=[], headers=[], **headers)`

A subclass of [`Request`](http.md#request) that encodes the provided body as
`application/json` and sets the appropriate headers.

Body must be data that is JSON-encodable.

## `TextRequest`
`class TextRequest(path='/', body='', *, method='GET', query=[], headers=[], **headers)`

A subclass of [`Request`](http.md#request) that encodes the provided body as
`text/plain` and sets the appropriate headers.

Body must be a string.

## `Response`
`class Response(body=b'', *, status=200, content_type=None, charset=None, boundary=None,headers=[], **headers)`

Represents a response from the application to a client.

Both `query` and `headers` expect a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

`body` can be `bytes`, an iterable of `bytes` or an async iterable of `bytes`.

`content_type`, `charset` and `boundary` together determine the `Content-Type`
header. If `content_type` starts with `'multipart/'` we expect `boundary` to be
present and add it to the `Content-Type`, otherwise `charset` gets added if
present.

This class implements [`Stream`](http.md#stream).

### Attributes
#### `status`
An integer representing the HTTP status code of the response.

#### `headers`
A [`Headers`](multidict.md#headers) object containing all response headers.

#### `ok`
A boolean indicating whether the response is considered 'ok' according to the
HTTP status code. This is implemented as `status < 400`.

## `FormResponse`
`class FormResponse(body={}, boundary=None, *, status=200, content_type=None, charset=None, headers=[], **headers)`

A subclass of [`Response`](http.md#response) that encodes the provided body as
`multipart/form-data` and sets the appropriate headers.

Body must be a `dict`, an iterable of 2-tuples or a 
[`MultiDict`](multidict.md#multidict) where the keys are strings and the values
are either strings or a [`File`](multipart.md#file).

If no `boundary` is supplied a `boundary` is automatically generated.

## `HtmlResponse`
`class HtmlResponse(body='', *, status=200, content_type=None, charset=None, headers=[], **headers)`

A subclass of [`Response`](http.md#response) that encodes the provided body as
`text/html` and sets the appropriate headers.

Body must be a string.

## `JsonResponse`
`class JsonResponse(body={}, *, status=200, content_type=None, charset=None, headers=[], **headers)`

A subclass of [`Response`](http.md#response) that encodes the provided body as
`application/json` and sets the appropriate headers.

Body must be data that is JSON-encodable.

## `RedirectResponse`
`class RedirectResponse(location, *, status=304, content_type=None, charset=None, headers=[], **headers)`

A subclass of [`Response`](http.md#response) that represents a redirect to the
provided `location`.

## `TextResponse`
`class Response(body='', *, status=200, content_type=None, charset=None, headers=[], **headers)`

A subclass of [`Response`](http.md#response) that encodes the provided body as
`text/plain` and sets the appropriate headers.

Body must be a string.

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
`chunks()`
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

### Methods
#### `accept`
`coroutine accept(headers=[], **headers)`

Accepts the connection with the provided response headers.

`headers` expects a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

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
