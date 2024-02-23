from utils import init_ton_client, get_seqno

import asyncio
from wallet import get_ton_wallet_from_mnemonic

from tonsdk.contract.token.ft import JettonWallet
from tonsdk.utils import to_nano, Address

from pytonlib import TonlibClient

import requests
from pathlib import Path


main_mnemonic = ["fantasy", "song", "lab", "false", "catalog", "crater", "lift", "romance", "mistake", "glass", "galaxy", "alcohol", "inform", "olive", "ensure", "exercise", "mushroom", "crop", "behave", "rescue", "nasty", "brass", "vintage", "scrub"]

async def mint():
    mnemonic, pub_add, priv_add, wallet = get_ton_wallet_from_mnemonic(main_mnemonic)


    wallet_address = wallet.address.to_string(is_user_friendly=True, is_url_safe=True, is_bounceable=True, is_test_only=True)
    contract_address = 'EQAkRwyPQswEQKYCwyv9qA52ggIRM2cnAeKR_AyhHTXyZ5qk'
    #NEED
    # query_id: Int as uint64;
    # amount: Int as coins;
    # destination: Address;
    # response_destination: Address;
    # custom_payload: Cell?;
    # forward_ton_amount: Int as coins;
    # forward_payload: Slice as remaining;

    # In lib
    # to_address: Address,
    # jetton_amount: int,
    # forward_amount: int = 0,
    # forward_payload: bytes = None,
    # response_address: Address = None,
    # query_id: int = 0

    body = JettonWallet().create_transfer_body(
        to_address=Address(wallet_address),
        jetton_amount=to_nano(100, 'ton'),
    )

    client = await init_ton_client()

    seqno = await get_seqno(client, wallet_address)

    query = wallet.create_transfer_message(to_addr=contract_address,
                                           amount=to_nano(0.05, 'ton'), seqno=seqno, payload=body)

    await client.raw_send_message(query['message'].to_boc(False))

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(mint())