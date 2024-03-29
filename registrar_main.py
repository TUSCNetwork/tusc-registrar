# Entry point to program.
# Handles setting up logging, config, and starting various services (DB, tusc...)
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# TODO: change to specific origins for production
CORS(app)
import log

logger = log.setup_custom_logger('root', 'registrar')
logger.debug('Starting TUSC registration server')

from tusc_api.webctrl_tusc_api import tusc_api
import db_access.db as db
from config import cfg

# REMOVE ME
from tusc_api import gate_tusc_api

general_cfg = cfg["general"]

if __name__ == '__main__':
    logger.debug('Starting server')
    try:
        db.initiate_database_connection()
        app.logger = logger
        app.register_blueprint(tusc_api)
        app.run(host='0.0.0.0', port=8080)
    except Exception as e:
        logger.error(f'Server experienced an error: {e}')
        logger.debug('Shutting down server')
        raise e
    logger.debug('Shutting down server')


