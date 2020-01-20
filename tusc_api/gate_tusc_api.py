import requests
import json
import logging
import db_access.db as db
import time
import subprocess
from config import cfg

logger = logging.getLogger('root')
logger.debug('loading')

DefaultErrorMessage = {"error": "Something went wrong, please contact tusc support"}
WalletRestartedErrorMessage = {"wallet-restarted": True}

ErrorCodeSuccess = 0
ErrorCodeFailedWithResponse = 1
ErrorCodeFailedMethodNameResponse = 2
ErrorCodeFailedRestartedWallet = 3

tusc_api_cfg = cfg["tusc_api"]
general_cfg = cfg["general"]
wallet_cfg = cfg["wallet"]

def build_request_dict(method_name: str, params: list) -> dict:
    tusc_wallet_command_structure = {
        "jsonrpc": tusc_api_cfg["tusc_wallet_rpc_version"],
        "method": method_name,
        "params": params,
        "id": 1
    }
    return tusc_wallet_command_structure


def get_tusc_url() -> str:
    return "http://" + \
           tusc_api_cfg["tusc_wallet_ip"] + ":" + \
           tusc_api_cfg["tusc_wallet_port"] + \
           tusc_api_cfg["tusc_wallet_rpc_endpoint"]


def suggest_brain_key() -> dict:
    resp, error = send_request("suggest_brain_key", [], True)

    if error == ErrorCodeFailedMethodNameResponse:
        # handle suggest_brain_key specific errors
        return DefaultErrorMessage
    else:
        return resp


def list_account_balances(account_name: str) -> dict:
    resp, error = send_request("list_account_balances", [account_name])

    if error == ErrorCodeFailedMethodNameResponse:
        # handle list_account_balances specific errors
        if "data" in resp["error"].keys():
            if "stack" in resp["error"]["data"].keys():
                for stack_obj in resp["error"]["data"]["stack"]:
                    if "format" in stack_obj:
                        if "rec && rec->name" in stack_obj["format"]:
                            return {"error": "Account name '" + account_name + "' could not be found. "}

        return DefaultErrorMessage
    else:
        return resp


def does_account_exist(account_name: str) -> bool:
    resp = list_account_balances(account_name)

    if "error" in resp:
        return False
    else:
        return True


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

    resp, error = send_request("register_account",
                               [account_name,
                                public_key,  # Owner
                                public_key,  # Active
                                tusc_api_cfg["registrar_account_name"],  # Registrar
                                ref,  # Referrer
                                75,
                                True], False)

    if error == ErrorCodeFailedMethodNameResponse:
        if "data" in resp["error"].keys():
            if "stack" in resp["error"]["data"].keys():
                for stack_obj in resp["error"]["data"]["stack"]:
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

        return DefaultErrorMessage
    elif error == ErrorCodeFailedRestartedWallet:
        return WalletRestartedErrorMessage
    else:
        db.save_completed_registration(account_name, public_key)
        return resp


def get_account(account_name: str) -> dict:
    resp, error = send_request("get_account", [account_name], True)

    if error == ErrorCodeFailedMethodNameResponse:
        return DefaultErrorMessage
    else:
        return resp


def get_account_public_key(account_name: str) -> str:
    resp, error = send_request("get_account", [account_name], True)

    if error == ErrorCodeFailedMethodNameResponse:
        return "ERROR"
    else:
        # find the account's public key and return that
        return resp["result"]["owner"]["key_auths"][0][0]


def send_request(method_name: str, params: list, do_not_log_data=False) -> (dict, int):
    if general_cfg["testing"]:
        if method_name == "get_account":
            return {"error": "TEST RESPONSE: failed"}, ErrorCodeSuccess
        if method_name == "transfer":
            return {}, ErrorCodeSuccess
        if method_name == "list_account_balances":
            return {}, ErrorCodeSuccess
        if method_name == "register_account":
            if params[0] == 'restart-wallet':
                restart_wallet()
                return {"error": "TEST RESPONSE: restarted wallet"}, ErrorCodeFailedRestartedWallet
            else:
                return {"error": "TEST RESPONSE: already in use"}, ErrorCodeSuccess

    # when error is ErrorCodeFailedWithResponse, pass back to caller.
    # When error is ErrorCodeFailedMethodNameResponse, handle per method_name
    req = build_request_dict(method_name, params)

    # POST with JSON
    command_json = json.dumps(req)
    logger.debug("Sending command to TUSC wallet")

    if do_not_log_data is False:
        logger.debug("Command payload: " + str(command_json))

    url = get_tusc_url()

    logger.debug("posting to: " + str(url))

    # TODO: Handle timeouts if wallet isn't online
    r = requests.post(url, data=command_json)

    try:
        api_response_json = json.loads(r.text)

        if "result" in api_response_json.keys():
            if do_not_log_data is False:
                logger.debug("Command response: " + str(api_response_json))
            return {"result": api_response_json["result"]}, ErrorCodeSuccess
        elif "error" in api_response_json.keys():
            logger.error("Error in response from TUSC api")
            logger.error("Command response: " + str(api_response_json))
            generic_errors_handled, error_code = handle_generic_tusc_errors(api_response_json)
            return generic_errors_handled, error_code
        else:
            logger.error("Unsure what happened with TUSC API")
            logger.error("Command response: " + str(api_response_json))

            return DefaultErrorMessage, ErrorCodeFailedWithResponse
    except json.JSONDecodeError as err:
        logger.error(err)
        return {"error": "Internal server error"}, ErrorCodeFailedWithResponse


def handle_generic_tusc_errors(api_response_json: dict) -> (dict, int):
    if "data" in api_response_json["error"].keys():
        if "stack" in api_response_json["error"]["data"].keys():
            for stack_obj in api_response_json["error"]["data"]["stack"]:
                if "format" in stack_obj:

                    # Wallet is locked
                    if "is_locked" in stack_obj["format"]:
                        logger.error("Cannot perform operation, TUSC Wallet is locked")
                        return DefaultErrorMessage, ErrorCodeFailedWithResponse
                if "data" in stack_obj:
                    if "msg" in stack_obj["data"]:
                        if "invalid state" in stack_obj["data"]["msg"]:
                            # Wallet in invalid state, needs to be restarted.
                            logger.error("Cannot perform operation, TUSC Wallet is in invalid state")

                            restart_wallet()

                            return DefaultErrorMessage, ErrorCodeFailedRestartedWallet

    return api_response_json, ErrorCodeFailedMethodNameResponse


def restart_wallet():
    logger.info("Stopping TUSC Wallet")
    base_cmd = 'screen -S cli -p 0 -X stuff '
    subprocess.call(base_cmd + '"^C"', shell=True)

    # Wait for it to die gracefully
    time.sleep(5)

    logger.info("Restarting TUSC Wallet")
    wallet_path_param = wallet_cfg["path"]
    chain_id_param = '--chain-id \"' + wallet_cfg["chain_id"] + '\" '
    node_address_param = '-s ' + wallet_cfg["node_address"] + ' -H 0.0.0.0:5071\n"'
    subprocess.call(base_cmd + '"' + wallet_path_param + ' ' + chain_id_param + node_address_param, shell=True)
    time.sleep(2)

    logger.info("Unlocking TUSC Wallet")
    subprocess.call(base_cmd + '"unlock ' + wallet_cfg["wallet_password"] + '\n"', shell=True)


logger.debug('loaded')
