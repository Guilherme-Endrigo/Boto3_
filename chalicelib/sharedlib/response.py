import simplejson
import os

from chalice import Response

from chalicelib.app import app


def make_response(status_code=200, headers={}, body=None, message=None, data=None, error_code=None, json=None):
    """
    ja define os headers padrão para evitar problema de CORS, default para CORS_ORIGIN no env.
    """
    default_headers = {
        "Access-Control-Allow-Origin": app.current_request.headers.get('Origin', os.getenv("CORS_ORIGIN")),
        "Content-type": "application/json",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "authorization,content-type",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    message_template = {
        'success': True,
        'status_code': status_code,
        'error_message': None,
        'error_code': str(error_code),
        'message': message
    }

    if body:
        message_template = body
    else:
        if status_code > 399:
            message_template['success'] = False
            message_template['message'] = None
            message_template['error_message'] = message
        elif message and type(message) is str:
            message_template['message'] = message

    if data is not None:
        message_template['data'] = data

    if json:
        return Response(
            body=json,
            status_code=status_code,
            headers={**default_headers, **headers}
        )
    else:
        return Response(
            body=simplejson.dumps(message_template, use_decimal=True),
            status_code=status_code,
            headers={**default_headers, **headers}
        )
