import boto3
import json
import os

def get_credentials_database():
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    get_secret_value_response = client.get_secret_value(
        SecretId=os.getenv('PGSQL_SECRET')
    )

    secrets_data = json.loads(get_secret_value_response.get('SecretString'))
    return secrets_data