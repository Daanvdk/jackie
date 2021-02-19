# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/daanvdk/jackie/releases/tag/v0.1.0
