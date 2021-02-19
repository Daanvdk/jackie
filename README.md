# ![Logo](https://raw.githubusercontent.com/daanvdk/jackie/master/logo.svg) Jackie
![Build Status](https://img.shields.io/github/workflow/status/daanvdk/jackie/Continuous%20Integration)
[![Coverage](https://img.shields.io/codecov/c/github/daanvdk/jackie)](https://codecov.io/gh/Daanvdk/jackie)
[![PyPI](https://img.shields.io/pypi/v/jackie)](https://pypi.org/project/jackie)

A minimal [ASGI](https://asgi.readthedocs.io/en/latest/) web framework.

```python
from jackie.router import Router
from jackie.http import TextResponse

app = Router()

@app.get('/')
async def hello_world(request):
    name = request.query.get('name', 'World')
    return TextResponse(f'Hello, {name}!')
```

More information can be found on the
[website](https://daanvdk.github.io/jackie).
