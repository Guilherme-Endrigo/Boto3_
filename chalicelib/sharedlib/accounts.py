import logging
import os

import requests


applog = logging.getLogger('accounts')
applog.setLevel(logging.DEBUG)


def check_jwt_on_accounts(token):
    endpoint = os.environ['ACCOUNTS3_VALIDATE_JWT'].replace('{token}', token)
    headers = {
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json',
        'channel': 'al'
    }
    r = requests.get(endpoint, headers=headers)

    if r.status_code != 200:
        applog.warning(f'Token not Found. Status code: {r.status_code}')
        return False, r.status_code

    applog.info(r.text)
    applog.info(f'Token Found and Checked in Accounts')
    return True, 200


def get_acta_id(current_request):
    url = os.getenv('ACCOUNTS_USERDATA_URL', '')
    req = requests.get(
        url=url,
        headers={
            "Authorization": current_request.headers['Authorization'],
            "Content-type": "application/json",
            "channel": "al"
        }
    )
    user_id = req.json()['acta_user_id']
    return user_id

