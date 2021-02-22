# Hello World
Here we provide a simple 'Hello, World!'-example:
```python
from jackie.router import Router
from jackie.http import Response

app = Router()

@app.get('/')
def hello_world(request):
    name = request.query.get('name', 'World')
    return Response(text=f'Hello, {name}!')
```

We start with creating a `Router`, this router is used to send requests to the
correct view based on the method and path of the request.

The `hello_world`-function is what we call a 'view'. This is a function that
accepts a request and returns a response. In this case we either get the name
from the query params or default to `'World'`.
