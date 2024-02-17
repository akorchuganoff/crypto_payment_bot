from db import session, User

from pytonlib import TonlibClient
import requests
from pathlib import Path
import asyncio
from tonsdk.utils import to_nano, from_nano
import time

from tonsdk.crypto import mnemonic_new
from tonsdk.contract.wallet import Wallets, WalletVersionEnum, WalletV3ContractR2
from tonsdk.utils import to_nano, bytes_to_b64str

from wallet import get_wallet_from_mnemonic
import json

def check_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        return False
    return True

def get_existed_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    return user

async def init_client():
    url = "https://ton.org/testnet-global.config.json"
    config = requests.get(url).json()

    keystore = "/tmp/ton_keystore"
    Path(keystore).mkdir(parents=True, exist_ok=True)

    client = TonlibClient(ls_index=1, config=config, keystore=keystore)

    await client.init()

    return client

async def init_wallet(wallet):
    client = await init_client()

    query = wallet.create_init_external_message()
    deploy_message = query["message"].to_boc(False)
    await client.raw_send_message(deploy_message)

async def get_seqno(client: TonlibClient, address:str):
    data =  await client.raw_run_method(method="seqno", stack_data=[], address=address)
    return int(data["stack"][0][1], 16)

async def get_user_ton_wallet(user):
    mnemonics = json.loads(user.ton_mnemonics)
    mnemonics, pub_k, priv_k, wallet = get_wallet_from_mnemonic(mnemonics)
    return wallet


async def send_transaction(wallet, address, amount, message):
    try:
        client = await init_client()
        seqno = await get_seqno(client, wallet.address.to_string(True, True, True, True))

        transfer_query = wallet.create_transfer_message(to_addr=address, amount=to_nano(amount, "ton"), seqno=seqno, payload=message)
        message = transfer_query["message"].to_boc(False)
        answer = await client.raw_send_message(message)

        print(answer)
        if answer["@type"] == "ok":
            return (True, "Транзакция исполнена")
        else:
            (False, f"Транзакция не исполнена по причине: {answer['@error']}")
    except Exception as e:
        return (False, f"Транзакция не исполнена по причине: {e}")
    
async def get_ton_wallet_balance(wallet: WalletV3ContractR2):
    client = await init_client()

    parameters = await client.raw_get_account_state(address=wallet.address.to_string(True, True, True, True))
    balance = from_nano(number=int(parameters["balance"]), unit="ton")
    return balance