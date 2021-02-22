This module provides a client that can be used to interact with an ASGI
application using a simple API.

## `Client`
`class Client(app)`

Initializes a client for the provided ASGI app `app`.

### Attributes
#### `cookies`
A dict mapping `str` to [`Cookie`](http.md#cookie) containing the cookies set
by the app. These cookies are sent as a `Cookie`-header on requests and
modified by `Set-Cookie`-headers on responses.

### Methods
#### `request`
`coroutine request(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine request(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine request(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine request(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Returns a response of type [Response](http.md#response) from the app for a
request described by the arguments.

Both `query` and `headers` expect a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

There are 4 parameters that can describe the body of the request. `form`,
`json`, `text` or `body`. At most one of these can be supplied and they
determine whether the request will be a [`FormRequest`](http.md#formrequest),
[`JsonRequest`](http.md#jsonrequest), [`TextRequest`](http.md#textrequest) or
[`Request`](http.md#request) respectively.

#### `get`
`coroutine get(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine get(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine get(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine get(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'GET'`.

#### `head`
`coroutine head(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine head(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine head(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine head(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'HEAD'`.

#### `post`
`coroutine post(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine post(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine post(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine post(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'POST'`.

#### `put`
`coroutine put(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine put(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine put(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine put(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'PUT'`.

#### `delete`
`coroutine delete(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine delete(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine delete(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine delete(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'DELETE'`.

#### `connect`
`coroutine connect(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine connect(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine connect(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine connect(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'CONNECT'`.

#### `options`
`coroutine options(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine options(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine options(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine options(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'OPTIONS'`.

#### `trace`
`coroutine trace(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine trace(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine trace(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine trace(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'TRACE'`.

#### `patch`
`coroutine patch(path='/', *, form, method='GET', query=[], headers=[], **headers)`  
`coroutine patch(path='/', *, json, method='GET', query=[], headers=[], **headers)`  
`coroutine patch(path='/', *, text, method='GET', query=[], headers=[], **headers)`  
`coroutine patch(path='/', *, body=b'', method='GET', query=[], headers=[], **headers)`

Shorthand for [`request`](client.md#request) where `method` defaults to `'PATCH'`.

#### `websocket`
`coroutine websocket(path='/', *, query=[], headers=[], **headers)`

Returns a socket of type [`Socket`](http.md#socket) with a websocket connection
to the app described by the arguments.

Both `query` and `headers` expect a `dict`, an iterable of 2-tuples or a
[`MultiDict`](multidict.md#multidict).

The returned socket differes from a normal [`Socket`](http.md#socket) in a few
aspects because it resembles the other side of the connection.

The `accept` coroutine will throw an error when called since it is not up to
this socket to accept. This is the responsibility of the app.

There are two extra coroutines called `accepted` and `closed` to be able to
wait on the app to respectively accept or close the connection.

`accepted` will return the response headers if accepted and otherwise throw a
[`Disconnect`](http.md#disconnect).

`closed` will return the close code if closed and otherwise throw an
AssertionError.
