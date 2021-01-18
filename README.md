# Jack
A minimal ASGI web framework.

```python
from jack.router import Router
from jack.http import TextResponse

app = Router()

@app.get('/')
async def hello_world(request):
    name = request.query.get('name', 'World')
    return TextResponse(f'Hello, {name}!')
```
