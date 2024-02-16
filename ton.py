# Requests for API, Asyncio to call sleep() in async func
import requests
import asyncio
from base64 import b64decode
from httpx import AsyncClient

# Aiogram
from aiogram import Bot
from aiogram.types import ParseMode

import config
from db import session
import utils


async def start():

    try:

        with open('last_lt.txt', 'r') as f:
            last_lt = int(f.read())
    except FileNotFoundError:

        last_lt = 0


    bot = Bot(token=config.BOT_TOKEN)

    while True:
        # 2 Seconds delay between checks
        await asyncio.sleep(2)

        # API call to Toncenter that returns last 100 transactions of our wallet
        resp = requests.get(f'{config.API_BASE_URL}/api/v2/getTransactions?'
                            f'address={config.DEPOSIT_ADDRESS}&limit=100&'
                            f'archival=true&api_key={config.API_KEY}').json()


        if not resp['ok']:
            continue

        for tx in resp['result']:

            lt, hash = int(tx['transaction_id']['lt']), tx['transaction_id']['hash']


            if lt <= last_lt:
                continue


            value = int(tx['in_msg']['value'])
            if value > 0:

                uid = tx['in_msg']['message']

                if not uid.isdigit():
                    continue

                uid = int(uid)
                ans = utils.check_user(uid)
                print(ans, uid)
                if not ans:
                    continue

                user = utils.get_existed_user(uid)
                user.ton_balance += value / 1e9
                session.commit()

                await bot.send_message(uid, 'Deposit confirmed!\n'
                                      f'*+{value / 1e9:.2f} TON*',
                                      parse_mode=ParseMode.MARKDOWN)

            last_lt = lt
            with open('last_lt.txt', 'w') as f:
                f.write(str(last_lt))


class HTTPMethods:
    GET = "GET"
    POST = "POST"

headers: dict = {"Authorization": f"Bearer {config.API_KEY}"}
_http_client: AsyncClient = AsyncClient(headers=headers)



class TONAPIBaseException(Exception):
    pass


async def _json_request(self, http_method: str, url: str, **request_kwargs) -> dict:
        return (
            await _http_client.request(method=http_method, url=url, **request_kwargs)
        ).json()



async def send_transaction(self, boc: str) -> str:
        
    headers: dict = {"Authorization": f"Bearer {config.API_KEY}"}
    _http_client: AsyncClient = AsyncClient(headers=headers)

    response_data: dict = await self._json_request(
        http_method=HTTPMethods.POST,
        url=config.SEND_TRANSACTION_API_URL,
        json=dict(boc=boc),
    )

    if "error" in response_data:
        raise TONAPIBaseException("Transaction send error")

    return b64decode(s=response_data["result"]["hash"]).hex()