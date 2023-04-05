import logging
from chalice import Chalice

app = Chalice(app_name='al-content-admin-taxonomy')
app.log.setLevel(logging.INFO)