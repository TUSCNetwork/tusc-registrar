import pytest
import copy
from tusc_api import gate_tusc_api
from config import wallet_cfg
import log

logger = log.setup_custom_logger('root', '')

wallet_cfg_backup = copy.deepcopy(wallet_cfg)

@pytest.fixture()
def setup_teardown():
    print("setup")
    yield None
    wallet_cfg = wallet_cfg_backup
    print("teardown")


# These tests aren't the best since it actually starts a real wallet which requires the
# target API node to be running but, assuming the node is running and available, it does prove things load properly
class TestWallet_success:
    def test_start_wallet(self):
        wallet_proc = gate_tusc_api.start_wallet()
        wallet_proc.kill()

    def test_start_wallet_loop(self):
        for x in range(5):
            wallet_proc = gate_tusc_api.start_wallet()
            wallet_proc.kill()

    def test_start_and_unlock_wallet(self):
        response = gate_tusc_api.start_and_unlock_wallet()
        assert response == gate_tusc_api.WalletUnlockResponseNoneResult

    def test_start_wallet_and_unlock_loop(self):
        for x in range(5):
            response = gate_tusc_api.start_and_unlock_wallet()
            assert response == gate_tusc_api.WalletUnlockResponseNoneResult

    def test_suggest_brain_key_with_exceptions(self):
        resp = gate_tusc_api.suggest_brain_key()
        assert 'result' in resp
        assert 'brain_priv_key' in resp['result']
        assert 'wif_priv_key' in resp['result']
        assert 'pub_key' in resp['result']

    def test_start_wallet_and_unlock_suggest_brain_key_loop(self):
        for x in range(5):
            response = gate_tusc_api.suggest_brain_key()
            assert 'result' in response
            assert 'brain_priv_key' in response['result']
            assert 'wif_priv_key' in response['result']
            assert 'pub_key' in response['result']

    def test_register_account_with_exceptions_account_not_linked_in_wallet(self, setup_teardown):
        response = gate_tusc_api.register_account(
            "asdqwert",
            "TUSC6mC3SQiFEcsGzrwUTMHKPKyyE2GdA1bAfKuzEcdst7sRZc6rhR",
            "registration-faucet"
        )
        assert response == gate_tusc_api.DefaultErrorResponse

    def test_start_wallet_http_error(self, setup_teardown):
        wallet_cfg["node_address"] = "wss://not.a.real.website/wallet"
        try:
            gate_tusc_api.start_wallet()
        except TimeoutError as e:
            assert str(e) == "Timed out while waiting for TUSC wallet to start"
            return
        pytest.fail("Should have caught exception")

    def test_suggest_brain_key_with_exceptions_invalid_wallet_address(self, setup_teardown):
        wallet_cfg["node_address"] = "wss://not.a.real.website/wallet"
        response = gate_tusc_api.suggest_brain_key()
        assert response == gate_tusc_api.DefaultErrorResponse

    def test_start_and_unlock_incorrect_password(self, setup_teardown):
        wallet_cfg["wallet_password"] = "incorrectpassword"
        response = gate_tusc_api.start_and_unlock_wallet()
        assert response == gate_tusc_api.DefaultErrorResponse

    def test_suggest_brain_key_with_exceptions_incorrect_password(self, setup_teardown):
        wallet_cfg["wallet_password"] = "incorrectpassword"
        response = gate_tusc_api.suggest_brain_key()
        assert response == gate_tusc_api.DefaultErrorResponse

    def test_register_account_with_exceptions_incorrect_password(self, setup_teardown):
        wallet_cfg["wallet_password"] = "incorrectpassword"
        response = gate_tusc_api.register_account(
            "asdqwert",
            "b",
            "c"
        )
        assert response == gate_tusc_api.DefaultErrorResponse