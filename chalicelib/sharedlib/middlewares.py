import json
import logging
import os

from chalice import Response

from .accounts import check_jwt_on_accounts

applog = logging.getLogger('app_middlewares')
applog.setLevel(level=logging.DEBUG)


def check_cors(event, get_response):
    """
    Ajusta os headers na chamada OPTIONS para evitar erro de CORS
    """

    if event.method.upper() == 'OPTIONS':
        return Response(
            headers={
                "Access-Control-Allow-Origin": event.headers.get('Origin', os.getenv("CORS_ORIGIN", default="https://publicacoes.empiricus.com.br")),
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                "Access-Control-Allow-Headers": "authorization,content-type",
                "Access-Control-Max-Age": "6000",
            },
            body=""
        )
    return get_response(event)


def handle_jwt(event, get_response):
    """
    Verifica no accounts se esse jwt é válido
    """

    if "authorization" not in event.headers:
        return Response(
            status_code=401,
            headers={'Content-type': 'application/json'},
            body=json.dumps({'message': 'Missing Authentication Token'})
        )

    default_headers = {
        "Access-Control-Allow-Origin": event.headers.get('Origin', os.getenv("CORS_ORIGIN")),
        "Content-type": "application/json",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers": "authorization,content-type",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    }

    token = event.headers.get('Authorization', 'Bearer ').replace('Bearer ', '')
    if not token or token.strip() == '':
        applog.error('Token {} is not authorized'.format(event.headers['Authorization']))
        return Response(status_code=401, headers=default_headers, body='Unauthorized')

    is_authenticated, code = check_jwt_on_accounts(token)
    code = 0

    if not is_authenticated:
        applog.error('Token {} is not authorized'.format(event.headers['Authorization']))
        return Response(status_code=code, headers=default_headers, body='Unauthorized')
    return get_response(event)
