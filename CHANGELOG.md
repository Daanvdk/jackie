# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- `jackie.http.Cookie` is a new class that contains information about setting
a cookie. It takes a name and a value but also parameters like `expires` and
`same_site`.
- `jackie.http.Request` now has an attribute `cookies` that contains a dict of
cookies.
- `jackie.http.Response` now takes a keyword argument `set_cookies` which
accepts an iterable of `jackie.http.Cookie`. These cookies will be added to the
response headers as `Set-Cookie`-headers.
- `jackie.http.Socket` now has an attribute `cookies` that contains a dict of
cookies.
- `jackie.http.Socket.accept` now takes a keyword argument `set_cookies` which
accepts an iterable of `jackie.http.Cookie`. These cookies will be added to the
response headers as `Set-Cookie`-headers.
- `jackie.client.Client` now has a `cookies` attribute that contains a dict of
cookies. These are automatically sent as a `Cookie`-header on requests and
modified by `Set-Cookie`-headers on responses.

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

[Unreleased]: https://github.com/daanvdk/jackie/compare/v0.1.0..HEAD
[0.1.0]: https://github.com/daanvdk/jackie/releases/tag/v0.1.0
