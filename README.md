# Jack
A minimal ASGI web framework.

```python
from jack.router import Router
from jack.http import HttpResponse

app = Router()

@app.get('/')
async def hello_world(request):
    name = request.query.get('name', 'World')
    return HttpResponse(f'Hello, {name}!')
```
