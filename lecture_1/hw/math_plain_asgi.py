import json
import math
from http import HTTPStatus

from urllib.parse import parse_qs

async def is_castable_to_positive_int(n, send):
    try:
        int_n = int(n)
    except ValueError:
        await send_data({"error": "Unprocessable entity"}, send, HTTPStatus.UNPROCESSABLE_ENTITY)
        return None
    
    if int_n < 0:
        await send_data({"error": "Bad request"}, send, HTTPStatus.BAD_REQUEST)
        return None
    return int_n
        


async def application(
        scope,
        receive,
        send
):
    if scope['method'] != 'GET':
        await send_data({"error": "Not Found"}, send, HTTPStatus.NOT_FOUND)
    path = scope['path']

    if path == "/factorial":
        n = parse_qs(scope.get('query_string', b'').decode()).get('n')
        if not n:
            await send_data({"error": "Unprocessable entity"}, send, HTTPStatus.UNPROCESSABLE_ENTITY)
            return
        int_n = await is_castable_to_positive_int(n[-1], send)
        if int_n is None:
            return  
        
        await send_data({'result': math.factorial(int_n)}, send)
    elif path.startswith('/fibonacci'):
        path_parts = scope['path'].split('/')
        if len(path_parts) < 3:
            await send_data({"error": "Unprocessable entity"}, send, HTTPStatus.UNPROCESSABLE_ENTITY)
            return
        
        int_n = await is_castable_to_positive_int(path_parts[2], send)
        if int_n is None:
            return
        

        a, b = 0, 1
        for _ in range(int_n):
            a, b = b, a + b
        await send_data({'result': b}, send)
    elif path == '/mean':
        body = await parse_request_body(receive)
        try:
            data = json.loads(body)
            if not isinstance(data, list) or not all(isinstance(x, (int, float)) for x in data):
                raise ValueError
        except (json.JSONDecodeError, ValueError):
            await send_data({"error": "Unprocessable entity"}, send, HTTPStatus.UNPROCESSABLE_ENTITY)
            return

        if not data:
            await send_data({"error": "Bad request"}, send, HTTPStatus.BAD_REQUEST)
            return

        result = sum(data) / len(data)
        await send_data({'result': result}, send)
    else:
        await send_data({"error": "Not Found"}, send, HTTPStatus.NOT_FOUND)
    
    

async def parse_request_body(receive):
    body = b''
    while True:
        msg = await receive()
        body += msg.get('body', b'')
        if not msg.get('more_body', False):
            break
    return body

async def send_data(data, send, status=HTTPStatus.OK):
    await send(
        {
            'type': 'http.response.start',
            'status': status,
            'headers': [
                (b'content-type', 'application/json')
            ],
        }
    )
    await send(
        {
            "type": 'http.response.body',
            "body":  json.dumps(data).encode(),
        }
    )

