This module provides the building blocks to work with HTTP in jackie.

## Request

## FormRequest

## JsonRequest

## TextRequest

## Response

## FormResponse

## HtmlResponse

## JsonResponse

## RedirectResponse

## TextResponse

## Socket

## Disconnect

## asgi_to_jackie
`asgi_to_jackie(app)`

Converts an ASGI application `app` into a jackie view.

If `app` was created by [`jackie_to_asgi`](#jackie_to_asgi) it will return the
original view instead.

## jackie_to_asgi
`asgi_to_jackie(view)`

Converts a jackie view `view` into an ASGI application.

If `view` was created by [`asgi_to_jackie`](#asgi_to_jackie) it will return the
original application instead.
