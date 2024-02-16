from db import session, User

from pytonlib import TonlibClient
import requests
from pathlib import Path
import asyncio
from tonsdk.utils import to_nano
import time

def check_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        return False
    return True

def get_existed_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    return user

async def init_wallet(wallet):
    url = "https://ton.org/testnet-global.config.json"
    config = requests.get(url).json()

    keystore = "/tmp/ton_keystore"
    Path(keystore).mkdir(parents=True, exist_ok=True)

    client = TonlibClient(ls_index=1, config=config, keystore=keystore)

    await client.init()
    query = wallet.create_init_external_message()
    deploy_message = query["message"].to_boc(False)
    await client.raw_send_message(deploy_message)


async def send_transaction(wallet, address, amount, message):
    try:
        url = "https://ton.org/testnet-global.config.json"
        config = requests.get(url).json()

        keystore = "/tmp/ton_keystore"
        Path(keystore).mkdir(parents=True, exist_ok=True)

        client = TonlibClient(ls_index=1, config=config, keystore=keystore)

        await client.init()

        transfer_query = wallet.create_transfer_message(to_addr=address, amount=to_nano(amount, "ton"), seqno=1, payload=message)
        message = transfer_query["message"].to_boc(False)
        print(message)
        await client.raw_send_message(message)
        return (True, "Транзакция исполнена")
    except Exception as e:
        return (False, f"Транзакция не исполнена по причине: {e}")