---
template: index.html
extra_css:
    - assets/stylesheets/index.css
hide:
    - navigation
---
```python
from jackie.router import Router
from jackie.http import Response

app = Router()

@app.get('/')
async def hello_world(request):
    name = request.query.get('name', 'World')
    return Response(text=f'Hello, {name}!')
```
