import json
import logging
import sys

from chalicelib.app import app


def add_log_message(message, type=logging.INFO):
    log_func = {
        logging.INFO: app.log.info,
        logging.DEBUG: app.log.debug
    }

    error_source = sys._getframe().f_back.f_code.co_name
    log_message = {'source': error_source, 'mensagem': message}

    log_func[type](json.dumps(log_message))

