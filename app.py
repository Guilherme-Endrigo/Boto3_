import boto3
import simplejson as json

from chalicelib.app import app
from chalicelib import parser
from chalicelib.postgres_interface import post_taxonomy_postgres, put_taxonomy_postgres, return_taxonomies, return_taxonomy, return_child_list, validate_new_taxonomy,validate_put_taxonomy, validate_update_order
from chalicelib.ddb_interface import get_user_id
from chalicelib.sharedlib.response import make_response
from chalicelib.sharedlib.middlewares import check_cors, handle_jwt
from chalicelib.sharedlib.accounts import get_acta_id

app.register_middleware(check_cors, 'http')
app.register_middleware(handle_jwt, 'http')


def validate_taxonomy_id(taxonomy_id):
    if not taxonomy_id:
        return None, {'message': "Deve-se informar um taxonomy_id.", 'status_code': 400}
            
    check_id = parser.check_uuid(taxonomy_id)

    if check_id is False:
        return None, {'message': "Taxonomy_id é inválido.", 'status_code': 400}
       
def validate_json(json_body):
    if not json_body:
        return None, {'message': f"Não foi enviado um Json", 'status_code': 500}

    _, error_dict = parser.validate_json_taxonomy(json_body)
    if error_dict:
        parser_error = json.dumps(error_dict)    
        app.log.info(f"Error logging user.Message body: {app.current_request.raw_body} Error: {parser_error}")   
        return None, {'message': f"Erro ao validar os dados. Error: {error_dict}", 'status_code': 400}
    
    else:
        return app.current_request.json_body, {'message': f"json validado. Enviado: {app.current_request.json_body}", 'status_code': 202}


@app.route('/taxonomies', methods=['GET', 'OPTIONS'])
def get_taxonomies():
    taxonomies, taxonomies_message = return_taxonomies()
    
    if not taxonomies:
        return make_response(
            status_code=taxonomies_message["status_code"], message=taxonomies_message["message"]
        )

    return make_response(
        status_code=taxonomies_message["status_code"], data=taxonomies
    )


@app.route('/taxonomy/{taxonomy_id}', methods=['GET'])
def get_taxonomy(taxonomy_id):
    validate_taxonomy_id(taxonomy_id)

    taxonomy, taxonomy_message = return_taxonomy(taxonomy_id)

    if not taxonomy:
        return make_response(
            status_code=taxonomy_message["status_code"], message=taxonomy_message["message"]
        )

    return make_response(
        status_code=taxonomy_message["status_code"], data=taxonomy
    )


@app.route('/taxonomy/child_list/{taxonomy_id}', methods=['GET', 'OPTIONS'])
def get_taxonomy_children(taxonomy_id):
    validate_taxonomy_id(taxonomy_id)
    taxonomy_children, taxonomy_children_message = return_child_list(taxonomy_id)

    if not taxonomy_children:
        return make_response(
            status_code=taxonomy_children_message["status_code"], message=taxonomy_children_message["message"]
        )

    return make_response(
        status_code=taxonomy_children_message["status_code"], data=taxonomy_children
    )


@app.route('/taxonomy', methods=['POST', 'OPTIONS'])
def post_taxonomy():
    
    json_body, json_body_message = validate_json(app.current_request.json_body)

    if not json_body:
       return make_response(
            status_code=json_body_message["status_code"], message=json_body_message["message"]
        )
    
    new_taxonomy = json_body

    acta_id = get_acta_id(app.current_request)
    app.log.info(f'acta_id: {acta_id}')
    
    user_status, user_id = get_user_id(str(acta_id))
    if user_status is not True:
        app.log.error(user_id['message'])
        return make_response(status_code=user_id['status_code'], message=user_id['message'])
    app.log.info(f'user_id: {user_id}')    
    
    taxonomy_obj, taxonomy_message = validate_new_taxonomy(new_taxonomy, user_id)
    
    if not taxonomy_obj:
        return make_response(
        status_code=taxonomy_message["status_code"], message=taxonomy_message["message"]
        )
    
    taxonomy, taxonomy_message = post_taxonomy_postgres(taxonomy_obj, new_taxonomy)
        
    if not taxonomy:
        return make_response(status_code=taxonomy_message["status_code"],message=taxonomy_message["message"])
    
    return make_response(status_code=taxonomy_message["status_code"], data=taxonomy)


@app.route('/taxonomy/{taxonomy_id}', methods=['PUT', 'OPTIONS'])
def put_taxonomy(taxonomy_id):
    print('aqui')
    validate_taxonomy_id(taxonomy_id)
    updated_taxonomy = app.current_request.json_body

    validated_taxonomy, taxonomy_obj_message = validate_put_taxonomy(updated_taxonomy)
    if not validated_taxonomy:
        return make_response(
            status_code=taxonomy_obj_message["status_code"], message=taxonomy_obj_message["message"]
        )
    
    acta_id = get_acta_id(app.current_request)
    app.log.info(f'acta_id: {acta_id}')
    
    user_status, user_id = get_user_id(str(acta_id))
    if user_status is not True:
        app.log.error(user_id['message'])
        return make_response(status_code=user_id['status_code'], message=user_id['message'])
    app.log.info(f'user_id: {user_id}')    
    

    taxonomy, taxonomy_message = put_taxonomy_postgres(validated_taxonomy, taxonomy_id, user_id)
    
    if not taxonomy:
        return make_response(status_code=taxonomy_message["status_code"],message=taxonomy_message["message"])
    
    return make_response(status_code=taxonomy_message["status_code"], message=taxonomy_message["message"])


@app.route('/taxonomy/order', methods=['PUT', 'OPTIONS'])
def order_taxonomy():
    updated_order = app.current_request.json_body

    validated_updated_order, validated_updated_order_message = validate_update_order(updated_order)
    
    if not validated_updated_order:
        return make_response(status_code=validated_updated_order_message["status_code"],message=validated_updated_order_message["message"])
    
    return make_response(status_code=validated_updated_order_message["status_code"], message=validated_updated_order_message["message"])