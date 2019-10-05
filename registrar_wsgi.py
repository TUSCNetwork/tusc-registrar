# Entry point to program for gunicorn.
# Handles setting up logging, config, and starting various services (DB, ethereum, tusc...)
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# TODO: change to specific origins for production
CORS(app)
import log

logger = log.setup_custom_logger('root', 'registrar')
logger.debug('Starting OCC to TUSC registration server')

from tusc_api.webctrl_tusc_api import tusc_api
import db_access.db as db
from config import cfg

general_cfg = cfg["general"]
logger.debug('Starting server')
db.initiate_database_connection()
app.logger = logger
app.register_blueprint(tusc_api)

if __name__ == '__main__':
    app.run()

