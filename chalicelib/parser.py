import os
import random

import uuid

import copy

TAXONOMY_FIELDS = [
    "taxonomy_name",
    "taxonomy_slug"
]

TAXONOMY_DATA_TYPES = {
    "taxonomy_name": str,
    "taxonomy_slug": str
}

GROUP_FIELDS = [
    "name"
]

GROUP_DATA_TYPES = {
    "name": str
}

def check_uuid(id):
    try:
        _ = uuid.UUID(id)
        return True
    except ValueError:
        return False


def _add_error(err_obj, field, err_message):
    if not field in err_obj:
        err_obj[field] = []
    err_obj[field].append(err_message)


def validate_json_structure(json_obj, expected_fields, expected_types):
    """
    validate the json_obj fields against a list of expected fields
    returns if the json_obj is valid, and an object
    """

    request_obj = copy.deepcopy(json_obj)
    error_dict = {}

    # clean all non-required fields
    keys_to_del = []
    for key in request_obj.keys():
        if not key in expected_fields:
            keys_to_del.append(key)
    for k in keys_to_del:
        del request_obj[k]

    # checking for missing fields
    for expected_field in expected_fields:
        if not expected_field in request_obj:
            _add_error(error_dict, expected_field, f'Campo {expected_field} não informado')
        else:
            # ver se o campo é do tipo certo, e se não está em branco
            if expected_types[expected_field] is uuid.UUID:
                try:
                    _ = uuid.UUID(request_obj[expected_field])
                except ValueError:
                    _add_error(
                        error_dict,
                        expected_field,
                        f'Campo {expected_field} com valor inválido')
            elif not isinstance(request_obj[expected_field], expected_types[expected_field]):
                _add_error(error_dict, expected_field, f'Campo {expected_field} não pode estar em branco')
            elif isinstance(request_obj[expected_field], (str, int)) and \
                    str(request_obj[expected_field]).strip() == "":
                _add_error(error_dict, expected_field, f'Campo {expected_field} com valor inválido')

            elif expected_field == 'location':
                if len(request_obj[expected_field]['location']) < 1:
                    _add_error(error_dict, expected_field,
                               f'Você precisa selecionar pelo menos uma {expected_field}')


    del request_obj
    return (error_dict == {}), error_dict


def validate_json_taxonomy(json_obj):
    # We'll not validate if it's a real user.
    # This should be done on the Builder

    if not isinstance(json_obj, dict):
        return False, {"all": "Tipo de objeto inválido"}

    expected_fields = TAXONOMY_FIELDS[:]

    ok_n, error_dict_n = validate_json_structure(json_obj, expected_fields, TAXONOMY_DATA_TYPES)

    if not ok_n:
        return False, error_dict_n

    return True, None


def validate_json_group(json_obj):
    # We'll not validate if it's a real user.
    # This should be done on the Builder

    if not isinstance(json_obj, dict):
        return False, {"all": "Tipo de objeto inválido"}

    expected_fields = GROUP_FIELDS[:]

    ok_n, error_dict_n = validate_json_structure(json_obj, expected_fields, GROUP_DATA_TYPES)

    if not ok_n:
        return False, error_dict_n

    return True, None