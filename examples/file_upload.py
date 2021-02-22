from jackie.router import Router
from jackie.http import Response


app = Router()


@app.get('/')
async def form(request):
    return Response(html=(
        '<!doctype html>\n'
        '<html lang="en">\n'
        '  <head>\n'
        '    <title>File Upload</title>\n'
        '  </head>\n'
        '  <body>\n'
        '    <form method="POST" action="/file_upload" '
        'enctype="multipart/form-data">\n'
        '      <input type="file" name="file" />\n'
        '      <button>Upload</button>\n'
        '    </form>\n'
        '  </body>\n'
        '</html>\n'
    ))


@app.post('/file_upload')
async def file_upload(request):
    form = await request.form()
    return Response(
        body=form['file'].content,
        content_type=form['file'].content_type,
    )
