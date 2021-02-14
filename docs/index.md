---
template: index.html
extra_css:
    - assets/stylesheets/index.css
hide:
    - navigation
---
```python
from jackie.router import Router
from jackie.http import TextResponse

app = Router()

@app.get('/')
async def hello_world(request):
    name = request.query.get('name', 'World')
    return TextResponse(f'Hello, {name}!')
```
