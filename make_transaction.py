from pytonlib import TonlibClient
import requests
from pathlib import Path
import asyncio
from tonsdk.utils import to_nano



async def send_transaction(client: TonlibClient, wallet, address, amount, message):
    transfer_query = wallet.create_transfer_message(to_addr=address, amount=to_nano(amount, "ton"), seqno=1, payload=message)
    message = transfer_query["message"].to_boc(False)
    await client.raw_send_message(message)


async def main():
    url = "https://ton.org/testnet-global.config.json"
    config = requests.get(url).json()

    keystore = "/tmp/ton_keystore"
    Path(keystore).mkdir(parents=True, exist_ok=True)

    client = TonlibClient(ls_index=1, config=config, keystore=keystore)

    await client.init()

    # mnemonics, pub_k, priv_k, wallet = create_wallet()

    # query = wallet.create_init_external_message()

    # deploy_message = query["message"].to_boc(False)

    # print_wallet(wallet)

    # await client.raw_send_message(deploy_message)
    await send_transaction(client=client, address="0QC_lg49-7GnVJY3PlJdJXHDjB1y8oNFrRPxwrIp3JkrD66H", amount=0.05, message="Перевод из кода")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())