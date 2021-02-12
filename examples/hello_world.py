from jackie.router import Router
from jackie.http import TextResponse


app = Router()


@app.get('/')
async def hello_world(request):
    name = request.query.get('name', 'World')
    return TextResponse(f'Hello, {name}!')
