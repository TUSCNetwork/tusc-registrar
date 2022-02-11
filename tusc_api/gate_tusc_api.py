import os
import requests
import json
import logging
import typing
import db_access.db as db
import subprocess
from config import tusc_api_cfg, wallet_cfg

logger = logging.getLogger('root')
logger.debug('loading')

DefaultErrorResponse = {"error": "Something went wrong, please contact tusc support"}
InternalServerErrorResponse = {"error": "Internal server error"}
WalletUnlockResponseNoneResult = {'result': None}


def build_request_dict(method_name: str, params: list) -> dict:
    tusc_wallet_command_structure = {
        "jsonrpc": tusc_api_cfg["tusc_wallet_rpc_version"],
        "method": method_name,
        "params": params,
        "id": 1
    }
    return tusc_wallet_command_structure


def get_tusc_url() -> str:
    return f'http://{tusc_api_cfg["tusc_wallet_ip"]}:{tusc_api_cfg["tusc_wallet_port"]}' \
           f'{tusc_api_cfg["tusc_wallet_rpc_endpoint"]}'


def suggest_brain_key() -> dict:
    wallet_response = start_and_unlock_wallet()
    if wallet_response != WalletUnlockResponseNoneResult:
        return wallet_response

    def suggest_brain_key_error_handler(api_response_json: dict, do_not_log_data: bool) -> dict:
        pass

    api_response_json = _send_request("suggest_brain_key", [], True)
    response = handle_generic_wallet_response(api_response_json, True, suggest_brain_key_error_handler)
    return response


def register_account(account_name: str, public_key: str, referrer: str) -> dict:
    # register_account <account_name> <owner-public_key> <active-public_key> <registrar_account>
    # <referrer_account> <referrer_percent> <broadcast>
    account_name_restrictions = "Account names must be more than 7 and less than 64 characters. " \
                                "They must consist of lower case characters, numbers, and '-'. " \
                                "They cannot start with a number."
    if len(account_name) < 8:
        return {"error": "Account name '" + account_name + "' is too short. " + account_name_restrictions}
    if len(account_name) > 63:
        return {"error": "Account name '" + account_name + "' is too long. " + account_name_restrictions}

    ref = tusc_api_cfg["registrar_account_name"]
    if referrer != "":
        ref = referrer

    wallet_response = start_and_unlock_wallet()
    if wallet_response != WalletUnlockResponseNoneResult:
        return wallet_response

    wallet_api_response = _send_request("register_account",
                             [account_name,
                              public_key,  # Owner
                              public_key,  # Active
                              tusc_api_cfg["registrar_account_name"],  # Registrar
                              ref,  # Referrer
                              75,
                              True], False)

    def register_account_error_handler(api_response_json: dict, do_not_log_data: bool) -> dict:
        return _register_account_error_handler_imp(api_response_json, account_name, account_name_restrictions, public_key)

    response = handle_generic_wallet_response(wallet_api_response, False, register_account_error_handler)
    if 'error' not in response:
        db.save_completed_registration(account_name, public_key)

    return response


def _register_account_error_handler_imp(api_response_json: dict,
                                        account_name: str,
                                        account_name_restrictions: str,
                                        public_key: str) -> dict:
    if "data" in api_response_json["error"].keys():
        if "stack" in api_response_json["error"]["data"].keys():
            for stack_obj in api_response_json["error"]["data"]["stack"]:
                if "format" in stack_obj:
                    if "rec && rec->name" in stack_obj["format"]:
                        return {"error": "Account name '" + account_name + "' already in use. "
                                                                           "Please use a different account name."}

                    if "is_valid_name(name" in stack_obj["format"]:
                        logger.error("Account name already exists")
                        return {"error": "Account name '" + account_name + "' is invalid. " +
                                         account_name_restrictions}

                    if "base58str.size() > prefix_len:" in stack_obj["format"]:
                        logger.error("Public key error")
                        return {"error": "The public key '" + public_key + "' is invalid. Please double check "
                                                                           "that it is correct and resubmit."}

    return DefaultErrorResponse


def unlock_wallet(password: str) -> dict:
    api_response_json = _send_request("unlock", [password], True)
    return handle_generic_wallet_response(api_response_json, True, None)


def _send_request(method_name: str, params: list, do_not_log_data=False) -> dict:
    req = build_request_dict(method_name, params)

    # POST with JSON
    command_json = json.dumps(req)
    logger.debug("Sending command to TUSC wallet")

    if do_not_log_data is False:
        logger.debug("Command payload: " + str(command_json))

    url = get_tusc_url()

    logger.debug("posting to: " + str(url))

    try:
        r = requests.post(url, data=command_json)
    except Exception as err:
        logger.error(err)
        raise err

    try:
        api_response_json = json.loads(r.text)
        return api_response_json

    except json.JSONDecodeError as err:
        logger.error(err)
        raise err


def handle_generic_wallet_response(
        api_response_json: dict,
        do_not_log_data: bool,
        error_handler_func: typing.Callable[[dict, bool], dict]) -> dict:
    response = None

    if "result" in api_response_json.keys():
        if do_not_log_data is False:
            logger.debug("Command response: " + str(api_response_json))
        response = {"result": api_response_json["result"]}
    elif "error" in api_response_json.keys():
        logger.error("Error in response from TUSC api")
        logger.error("Command response: " + str(api_response_json))
        response = handle_generic_tusc(api_response_json)

    if error_handler_func is not None and response is None:
        response = error_handler_func(api_response_json, do_not_log_data)

    if response is None:
        logger.error("Unsure what happened with TUSC API")
        logger.error("Command response: " + str(api_response_json))
        response = DefaultErrorResponse

    return response


def handle_generic_tusc(api_response_json: dict) -> dict:
    if "data" in api_response_json["error"].keys():
        if "stack" in api_response_json["error"]["data"].keys():
            for stack_obj in api_response_json["error"]["data"]["stack"]:
                if "format" in stack_obj:

                    # Wallet is locked
                    if "is_locked" in stack_obj["format"]:
                        logger.error("Cannot perform operation, TUSC Wallet is locked")
                        return DefaultErrorResponse

                    # Incorrect password used on wallet
                    if "during aes 256" in stack_obj["format"]:
                        logger.error("Cannot perform operation, "
                                     "incorrect wallet password, TUSC Wallet cannot be unlocked")
                        return DefaultErrorResponse

                if "data" in stack_obj:
                    if "msg" in stack_obj["data"]:
                        if "invalid state" in stack_obj["data"]["msg"]:
                            # Wallet in invalid state, needs to be restarted.
                            logger.error("Cannot perform operation, TUSC Wallet is in invalid state")
                            return DefaultErrorResponse

    return None


def start_wallet() -> subprocess:
    logger.info("Starting TUSC Wallet")

    wallet_proc = subprocess.Popen(
        [
            os.path.expanduser(wallet_cfg["path"]),
            '-s',
            wallet_cfg["node_address"],
            '--chain-id',
            wallet_cfg["chain_id"],
            '-H',
            '0.0.0.0:5071',
            '-w',
            os.path.expanduser(wallet_cfg["wallet_config_file"]),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    wallet_proc.stdin.flush()
    successfully_started_message = 'Listening for incoming HTTP and WS RPC requests'
    http_issue = 'Invalid HTTP status'
    for x in range(4):
        wallet_stderr = wallet_proc.stderr.readline().decode('ascii').rstrip()

        logger.info(f"TUSC Wallet stderr: {wallet_stderr}")
        if successfully_started_message in wallet_stderr:
            logger.info("TUSC Wallet started successfully")
            return wallet_proc
        elif http_issue in wallet_stderr:
            logger.error("TUSC Wallet failed to start due to an HTTP error")
            raise Exception("TUSC Wallet failed to start due to an HTTP error")

    raise TimeoutError("Timed out while waiting for TUSC wallet to start")


def start_and_unlock_wallet() -> dict:
    try:
        start_wallet()
    except Exception as e:
        logger.error(f"Error starting wallet: {str(e)}")
        return DefaultErrorResponse

    return unlock_wallet(wallet_cfg["wallet_password"])


logger.debug('loaded')
