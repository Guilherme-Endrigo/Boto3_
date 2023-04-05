import os

import boto3
from boto3.dynamodb.conditions import Key

users_table = boto3.resource('dynamodb').Table(os.environ['TABLE_USERS'])

def get_user_id(acta_id):
    try:
        user_query = users_table.query(
            KeyConditionExpression=Key('acta-id').eq(acta_id)
        )
        if len(user_data := user_query['Items']) != 0:
            user_info = next(iter(user_data))
            return True, user_info['user-id']

        return False, {'message': 'User ID Not Found', 'status_code': 404}

    except Exception as error:
        print(f'Error Found when Retrieving User-ID')
        return False, {'message': f'{error}', 'status_code': 500}