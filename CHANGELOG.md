# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
### Added
- `jackie.http.Request` and `jackie.http.Response` now accept a `file`-keyword
argument to specify their body. This takes a path to a file and will guess the
default content type based on the file's name. This will also use the
[`http.response.zerocopysend`](https://asgi.readthedocs.io/en/latest/extensions.html#zero-copy-send)
extension if available.
### Fixed
- `Disconnect` is now correctly exposed from `jackie.http`.

## [0.2.0] - 2021-02-22
### Added
- `jackie.http.Cookie` is a new class that contains information about setting
a cookie. It takes a name and a value but also parameters like `expires` and
`same_site`.
- `jackie.http.Request` now has an attribute `cookies` that contains a dict of
cookies.
- `jackie.http.Response` now takes a keyword argument `set_cookies` which
accepts an iterable of `jackie.http.Cookie`. These cookies will be added to the
response headers as `Set-Cookie`-headers.
- `jackie.http.Respones` now takes a keyword argument `unset_cookies` which
accepts an iterable of strings. These strings will be used as names for
`Set-Cookie` response headers that unset the cookie.
- `jackie.http.Socket` now has an attribute `cookies` that contains a dict of
cookies.
- `jackie.http.Socket.accept` now takes a keyword argument `set_cookies` which
accepts an iterable of `jackie.http.Cookie`. These cookies will be added to the
response headers as `Set-Cookie`-headers.
- `jackie.http.Socket.accept` now takes a keyword argument `unset_cookies`
which accepts an iterable of strings. These strings will be used as names for
`Set-Cookie` response headers that unset the cookie.
- `jackie.client.Client` now has a `cookies` attribute that contains a dict of
cookies. These are automatically sent as a `Cookie`-header on requests and
modified by `Set-Cookie`-headers on responses.
- `jackie.router.Router` now has a `websocket_not_found` method that sets a
view for when no view could be found for a websocket connection.
- `jackie.router.Request` now can also take `form`, `json` or `text` to specify
the body of the request.
- `jackie.router.Response` now can also take `form`, `json`, `text`, `html` or
`redirect` to specify the body of the response.

### Removed
- `jackie.http.FormRequest`, `jackie.http.JsonRequest` and
`jackie.http.TextRequest` were removed in favor of the new `form`, `json` and
`text` parameters on `jackie.http.Request`.
- `jackie.http.FormResponse`, `jackie.http.JsonRespone`,
`jackie.http.HtmlResponse`, `jackie.http.RedirectResponse` and
`jackie.http.TextRequest` were removed in favor of the new `form`, `json`,
`html`, `redirect` and `text` parameters on `jackie.http.Response`.


## [0.1.0] - 2021-02-16
### Added
- A HTTP API using `Request` and `Response` objects or a `Socket` object in
case of websockets that can be used interchangably with ASGI because of the
functions `jackie_to_asgi` and `asgi_to_jackie` that allow conversion between
the two.
- A `Router` class that makes it easy to create a routed ASGI application that
uses the HTTP API described above for the implementation of it's endpoints.
- A `Client` that makes it easy to interact with ASGI applications for purposes
like testing.

[0.2.0]: https://github.com/daanvdk/jackie/compare/v0.1.0..v0.2.0
[0.1.0]: https://github.com/daanvdk/jackie/releases/tag/v0.1.0
