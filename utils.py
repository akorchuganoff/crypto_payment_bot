from db import session, User

from pytonlib import TonlibClient
import requests
from pathlib import Path
import asyncio
from tonsdk.utils import to_nano, from_nano
import time

import unicodedata

from tonsdk.crypto import mnemonic_new
from tonsdk.contract.wallet import Wallets, WalletVersionEnum, WalletV3ContractR2
from tonsdk.utils import to_nano, bytes_to_b64str

from wallet import get_ton_wallet_from_mnemonic
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware

def check_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        return False
    return True

def get_existed_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    return user

async def init_ton_client():
    url = "https://ton.org/testnet-global.config.json"
    config = requests.get(url).json()

    keystore = "/tmp/ton_keystore"
    Path(keystore).mkdir(parents=True, exist_ok=True)

    client = TonlibClient(ls_index=6, config=config, keystore=keystore)

    await client.init()

    return client

async def init_bnb_client():
    bsc = "https://data-seed-prebsc-1-s1.binance.org:8545"
    w3 = Web3(Web3.HTTPProvider(bsc))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3.eth.account.enable_unaudited_hdwallet_features()
    return w3

async def create_bnb_wallet():
    w3 = await init_bnb_client()
    wallet, mnemonics = w3.eth.account.create_with_mnemonic()
    return wallet, mnemonics

async def get_bnb_wallet_from_mnemonics(mnemonics):
    w3 = await init_bnb_client()
    account = w3.eth.account.from_mnemonic(mnemonics)
    return account

async def init_bnb_wallet(wallet):
    pass

async def get_user_bnb_wallet(user: User):
    mnemonics = user.bnb_mnemonics
    wallet = await get_bnb_wallet_from_mnemonics(mnemonics)
    return wallet

async def send_bnb_transaction(wallet, address, amount, message):
    # try:
    w3 = await init_bnb_client()
    
    from_address = w3.to_checksum_address(wallet.address)
    to_address = w3.to_checksum_address(address)

    private_key = wallet._private_key.hex()  # hex адрес


    gas_price = w3.eth.gas_price
    gas = w3.to_wei(0.1, 'gwei')
    nonce = w3.eth.get_transaction_count(from_address)

    transaction = {
            'chainId': w3.eth.chain_id,
            'from': from_address,
            'to': to_address,
            'value': int(w3.to_wei(amount, 'ether')),
            'nonce': nonce, 
            'gasPrice': w3.to_wei(50, 'gwei'),
            'gas': 21000
        }


    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)


    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    return f"Транзакция отправлена. Хэш транзакции: {txn_hash.hex()}"

    # except Exception as e:
    #     return f"Транзакция не отправлена по причине:\n{e}"

async def get_bnb_wallet_balance(wallet):
    w3 = await init_bnb_client()
    
    address = wallet.address
    private_key = wallet._private_key

    checksum_address = Web3.to_checksum_address(address)
    balance = w3.eth.get_balance(checksum_address)

    result = w3.from_wei(balance,'ether')
    return result

async def init_ton_wallet(wallet):
    client = await init_ton_client()

    query = wallet.create_init_external_message()
    deploy_message = query["message"].to_boc(False)
    await client.raw_send_message(deploy_message)

async def get_seqno(client: TonlibClient, address:str):
    data =  await client.raw_run_method(method="seqno", stack_data=[], address=address)
    return int(data["stack"][0][1], 16)

async def get_user_ton_wallet(user):
    mnemonics = json.loads(user.ton_mnemonics)
    mnemonics, pub_k, priv_k, wallet = get_ton_wallet_from_mnemonic(mnemonics)
    return wallet

async def send_ton_transaction(wallet, address, amount, message):
    try:
        client = await init_ton_client()
        seqno = await get_seqno(client, wallet.address.to_string(True, True, True, True))

        transfer_query = wallet.create_transfer_message(to_addr=address, amount=to_nano(amount, "ton"), seqno=seqno, payload=message)
        message = transfer_query["message"].to_boc(False)
        answer = await client.raw_send_message_return_hash(message)
        print(answer)
        return f"Транзакция отправлена. Хеш транзакции:\n{answer['hash']}"
    except Exception as e:
        return (f"Транзакция не исполнена по причине: {e}")
    
async def get_ton_wallet_balance(wallet: WalletV3ContractR2):
    client = await init_ton_client()

    parameters = await client.raw_get_account_state(address=wallet.address.to_string(True, True, True, True))
    print(parameters)
    if int(parameters["balance"]) > 0:
        balance = from_nano(number=int(parameters["balance"]), unit="ton")
    elif int(parameters["balance"]) == 0:
        balance = 0
    else:
        balance = -1
    return balance