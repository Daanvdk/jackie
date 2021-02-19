This module provides some utility classes for working with multipart form data.

## `File`
`class File(name, content_type, content)`

This class is used to represent a file in multipart form data.

`name` must a be string representing the file name.

`content_type` must be a string comparable to a `Content-Type` request header.
Notably this includes metadata like `charset` and `boundary`.

`content` must be the contents of the file as `bytes`.

### Attributes
#### `name`
The name of the file.

#### `content_type`
The basic content type without any metadata like the charset.

#### `charset`
The charset of the content.

#### `boundary`
The boundary of the content. This is mostly relevant for `multipart` content
types.

#### `content`
The contents of the file as `bytes`.
