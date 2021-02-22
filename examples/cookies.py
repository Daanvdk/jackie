from jackie.router import Router
from jackie.http import Response, Cookie


app = Router()


@app.get('/')
async def hello_world(request):
    count = int(request.cookies.get('count', '0')) + 1
    return Response(
        text=f'count: {count}',
        set_cookies=[Cookie('count', str(count))],
    )
