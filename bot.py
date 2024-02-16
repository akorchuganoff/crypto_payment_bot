# Aiogram imports
from aiogram import Bot, Dispatcher, types

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
                          InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

import config

from web3 import Web3

from telegram import Update
from db import session, User

import ton
import json

from wallet import create_wallet, get_wallet_from_mnemonic
from utils import send_transaction, init_wallet



w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


async def get_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        user = User(user_id=user_id, ton_balance=0, bnb_balance=0, lt_balance=0, risk_amount=0)
        session.add(user)
        session.commit()
    return user


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):

    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    if user is None:
        mnemonics, pub_k, priv_k, wallet = create_wallet()

        user = User(user_id=message.from_user.id, ton_balance=0, bnb_balance=0, lt_balance=0, risk_amount=0, ton_mnemonics=json.dumps(mnemonics), init_ton_flag=False)
        session.add(user)
        session.commit()
        await bot.send_message(user.user_id, f"Вы зарегистрировались. Ваш пользователь выглядит так:\n{user.user_id}\n{user.ton_mnemonics}")
    else:
        await bot.send_message(user.user_id, f"Log IN. Ваш пользователь выглядит так:\n{user.user_id}\n{user.ton_mnemonics}")

def risk(message: types.Message):
    pass


def block(message: types.Message):
    pass

@dp.message_handler(commands='balance')
async def balance(message: types.Message):
    user = await get_user(message.from_user.id)
    await bot.send_message(user.user_id, f"Balance:\nTON: {user.ton_balance}\nBNB: {user.bnb_balance}\nLT: {user.lt_balance}")


@dp.message_handler(commands='deposit')
async def deposit_handler(message: types.Message):

    uid = message.from_user.id

    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    if user is None:
        await message.answer("Пользователь на зарегистрирован. Выполните регистрацию командой старт")
    else:
        mnemonics = json.loads(user.ton_mnemonics)
        mnemonics, pub_k, priv_k, wallet = get_wallet_from_mnemonic(mnemonics)

        deposit_address = wallet.address.to_string(is_user_friendly=True, is_url_safe=True, is_bounceable=True, is_test_only=True)


        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton('Deposit',
                                    #   url=f'ton://transfer/{config.DEPOSIT_ADDRESS}&text={uid}')
                                    url=f'ton://transfer/{deposit_address}')
        keyboard.add(button)

        # Send text that explains how to make a deposit into bot to user
        await message.answer('It is very easy to top up your balance here.\n'
                            'Simply send any amount of TON to this address:\n\n'
                            f'`{deposit_address}`\n\n'
                            f'And include the following comment: `{uid}`\n\n'
                            'You can also deposit by clicking the button below.',
                            reply_markup=keyboard)


class WithdrawState(StatesGroup):
    waiting_for_wallet_address = State()
    waiting_for_withdraw_amount= State()
    waiting_for_confirmation = State()


# Обработчик команды /withdraw
@dp.message_handler(commands="withdraw", state="*")
async def withdraw_command(message: types.Message, state: FSMContext):
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    if not user.init_ton_flag:
        mnemonics = json.loads(user.ton_mnemonics)
        mnemonics, pub_k, priv_k, wallet = get_wallet_from_mnemonic(mnemonics)
        await init_wallet(wallet)
        await message.answer("Кошелек был проинициализирован. Повторите запрос")
        await state.finish()
        user.init_ton_flag = True
        session.commit()
    else:
        await message.answer("Введите адрес вашего кошелька:")
        await state.set_state(WithdrawState.waiting_for_wallet_address.state)

# Обработчик ввода адреса кошелька
@dp.message_handler(state=WithdrawState.waiting_for_wallet_address.state)
async def process_wallet_address(message: types.Message, state: FSMContext):
    wallet_address = message.text
    await state.update_data(wallet_address = message.text)
    await message.answer(f"Вы ввели адрес кошелька: {wallet_address}.\nВведите количество в TON")
    await state.set_state(WithdrawState.waiting_for_withdraw_amount.state)
    print("Установил состояние жду количество")


@dp.message_handler(state=WithdrawState.waiting_for_withdraw_amount.state)
async def process_wallet_address(message: types.Message, state: FSMContext):
    amount = message.text
    await state.update_data(amount = message.text)

    data = await state.get_data()

    await message.answer(f"Вы ввели адрес кошелька: {data['wallet_address']}\nВывести следующее число TON: {data['amount']}\n Подтвердите [yes/no]")
    await state.set_state(WithdrawState.waiting_for_confirmation.state)

@dp.message_handler(state=WithdrawState.waiting_for_confirmation.state)
async def process_wallet_address(message: types.Message, state: FSMContext):
    confirmation = message.text
    
    if confirmation != "yes":
        await message.answer("Транзакция отменена")
    else:

        user = session.query(User).filter_by(user_id=message.from_user.id).first()

        mnemonics = json.loads(user.ton_mnemonics)
        mnemonics, pub_k, priv_k, wallet = get_wallet_from_mnemonic(mnemonics)

        print(mnemonics)

        data = await state.get_data()

        ans = await send_transaction(wallet=wallet, address=data["wallet_address"], amount=float(data["amount"]), message="Transaction from bot")

        await message.answer(ans[1])
        
        await state.finish()


if __name__ == '__main__':
    ex = executor.Executor(dp)
    # ex.loop.create_task(ton.start())
    ex.start_polling()