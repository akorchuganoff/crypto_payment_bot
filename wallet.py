from tonsdk.crypto import mnemonic_new
from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from tonsdk.utils import to_nano, bytes_to_b64str


def create_wallet():
    version = WalletVersionEnum.v3r2
    wc = 0
    mnemonics, pub_k, priv_k, wallet = Wallets.create(version=version, workchain=wc)

    return mnemonics, pub_k, priv_k, wallet

def get_wallet_from_mnemonic(mnemonics):
    version = WalletVersionEnum.v3r2
    wc = 0
    mnemonics, pub_k, priv_k, wallet = Wallets.from_mnemonics(mnemonics=mnemonics, version=version, workchain=wc)

    return mnemonics, pub_k, priv_k, wallet

def print_wallet(wallet):
    print("Testnet: ", wallet.address.to_string(is_user_friendly=True, is_url_safe=True, is_bounceable=True, is_test_only=True))
    print("Mainnet: ", wallet.address.to_string(is_user_friendly=True, is_url_safe=True, is_bounceable=True, is_test_only=False))


if __name__ == "__main__":
    mnemonics = ['interest', 'very', 'shoe', 'brass', 'theme', 'journey', 'margin', 'mule', 'sugar', 'hard', 'source', 'medal', 'coconut', 'room', 'scan', 'misery', 'verb', 'member', 'coconut', 'depth', 'waste', 'index', 'resist', 'vault']
    mnemonics, pub_k, priv_k, wallet = get_wallet_from_mnemonic(mnemonics)

    print(mnemonics)
    print_wallet(wallet)