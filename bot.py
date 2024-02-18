# Aiogram imports
from aiogram import Bot, Dispatcher, types

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
                          InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
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

from wallet import create_ton_wallet, get_ton_wallet_from_mnemonic
from utils import send_ton_transaction, init_ton_wallet, get_ton_wallet_balance, get_user_ton_wallet
from utils import create_bnb_wallet, get_bnb_wallet_from_mnemonics, get_user_bnb_wallet, get_bnb_wallet_balance, send_bnb_transaction


bsc = "https://data-seed-prebsc-1-s1.binance.org:8545"
w3 = Web3(Web3.HTTPProvider(bsc))

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


async def get_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    return user


@dp.message_handler(commands=['start', 'help'], state="*")
async def start(message: types.Message, state=FSMContext):
    await state.finish()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    if user is None:
        mnemonics_ton, pub_k_ton, priv_k_ton, wallet_ton = create_ton_wallet()
        wallet_bnb, mnemonics_bnb = await create_bnb_wallet()
        print(mnemonics_bnb)

        user = User(user_id=message.from_user.id, ton_balance=0, bnb_balance=0, lt_balance=0, risk_amount=0, ton_mnemonics=json.dumps(mnemonics_ton), init_ton_flag=False, bnb_mnemonics=mnemonics_bnb)
        session.add(user)
        session.commit()
        await message.answer("Welcome to WP. Layer0 mining/trading crosschain bridge.")
        # await bot.send_message(user.user_id, f"Зарегистрировался user_id: {user.user_id}, ton_mnemonics: {user.ton_mnemonics}\nbnb_mnemonics: {user.bnb_mnemonics}")
    else:
        await message.answer("Welcome to WP. Layer0 mining/trading crosschain bridge.")
        # await bot.send_message(user.user_id, f"LOG IN user_id: {user.user_id},\nton_mnemonics: {user.ton_mnemonics}\nbnb_mnemonics: {user.bnb_mnemonics}")

def risk(message: types.Message):
    pass


def block(message: types.Message):
    pass

@dp.message_handler(commands='balance', state="*")
async def balance(message: types.Message, state=FSMContext):
    await state.finish()
    user = await get_user(message.from_user.id)

    ton_wallet = await get_user_ton_wallet(user)
    ton_balance = await get_ton_wallet_balance(ton_wallet)

    bnb_wallet = await get_user_bnb_wallet(user)
    bnb_balance = await get_bnb_wallet_balance(bnb_wallet)

    if ton_balance == -1:
        ton_balance = "Кошелек не инициализирован. Пополните его на любую сумму"
    elif user.ton_balance != ton_balance and ton_balance >= 0:
        user.ton_balance = ton_balance
        session.commit()

    if user.bnb_balance != bnb_balance:
        user.bnb_balance = bnb_balance
        session.commit()

    await bot.send_message(user.user_id, f"Balance:\nTON: {ton_balance}\nBNB: {bnb_balance}\nLT: {user.lt_balance}")


@dp.message_handler(commands='deposit', state="*")
async def deposit_handler(message: types.Message, state=FSMContext):
    await state.finish()
    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    if user is None:
        await message.answer("Пользователь не зарегистрирован. Выполните регистрацию командой старт")
    else:
        ton_wallet = await get_user_ton_wallet(user)
        bnb_wallet = await get_user_bnb_wallet(user)

        ton_deposit_address = ton_wallet.address.to_string(is_user_friendly=True, is_url_safe=True, is_bounceable=True, is_test_only=True)
        bnb_deposit_address = bnb_wallet.address

        keyboard = InlineKeyboardMarkup()
        button = InlineKeyboardButton('Пополнить TON',
                                    url=f'ton://transfer/{ton_deposit_address}')
        keyboard.add(button)

        # Send text that explains how to make a deposit into bot to user
        await message.answer('Пополнить TON кошелек можно по адресу:\n\n'
                            f'`{ton_deposit_address}`\n\n'
                            'Пополнить BNB кошелек можно по адресу\n\n'
                            f'`{bnb_deposit_address}`\n\n'
                            'Также можно пополнить TON кошелек по кнопке',
                            reply_markup=keyboard)
        


class WithdrawState(StatesGroup):
    waiting_for_currency_choosing = State()

    ton_process_beginning = State()
    bnb_process_beginning = State()

    waiting_for_ton_wallet_address = State()
    waiting_for_withdraw_ton_amount= State()
    waiting_for_confirmation_ton = State()

    waiting_for_bnb_wallet_address = State()
    waiting_for_withdraw_bnb_amount= State()
    waiting_for_confirmation_bnb = State()


# Обработчик команды /withdraw
@dp.message_handler(commands="withdraw", state="*")
async def process_ton_wallet_beginning(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton('Вывести TON'), KeyboardButton('Вывести BNB'))

    ton_wallet = await get_user_ton_wallet(user)
    ton_balance = await get_ton_wallet_balance(ton_wallet)

    bnb_wallet = await get_user_bnb_wallet(user)
    bnb_balance = await get_bnb_wallet_balance(bnb_wallet)

    await message.answer(f"Ваши балансы:\n\tTON:{ton_balance}\n\tBNB: {bnb_balance}")
    
    await message.answer("Какую валюту вывести:", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text in ['Вывести TON', 'Вывести BNB'], state='*')
async def handle_button_click(message: types.Message, state: FSMContext):
    if message.text == 'Вывести TON':
        await WithdrawState.ton_process_beginning.set()
        await process_ton_wallet_beginning(message, state)
    elif message.text == 'Вывести BNB':
        await WithdrawState.bnb_process_beginning.set()
        await process_bnb_wallet_beginning(message, state)


@dp.message_handler(state=WithdrawState.ton_process_beginning.state)
async def process_ton_wallet_beginning(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if not user.init_ton_flag:
        wallet = await get_user_ton_wallet(user)

        await init_ton_wallet(wallet)
        await message.answer("Кошелек был проинициализирован. Повторите запрос", reply_markup=ReplyKeyboardRemove())
        await state.finish()
        user.init_ton_flag = True
        session.commit()
    else:
        wallet = await get_user_ton_wallet(user)
        await message.answer(f"Баланс кошелька TON: {await get_ton_wallet_balance(wallet)}", reply_markup=ReplyKeyboardRemove())
        await message.answer("Введите адрес вашего кошелька:")
        await state.set_state(WithdrawState.waiting_for_ton_wallet_address.state)

# Обработчик ввода адреса кошелька
@dp.message_handler(state=WithdrawState.waiting_for_ton_wallet_address.state)
async def process_ton_wallet_address(message: types.Message, state: FSMContext):
    wallet_address = message.text
    await state.update_data(wallet_address = message.text)
    await message.answer(f"Вы ввели адрес кошелька: {wallet_address}.\nВведите количество в TON")
    await state.set_state(WithdrawState.waiting_for_withdraw_ton_amount.state)
    print("Установил состояние жду количество")


@dp.message_handler(state=WithdrawState.waiting_for_withdraw_ton_amount.state)
async def process_ton_wallet_amount(message: types.Message, state: FSMContext):
    amount = message.text
    await state.update_data(amount = message.text)

    data = await state.get_data()

    await message.answer(f"Вы ввели адрес кошелька: {data['wallet_address']}\nВывести следующее число TON: {data['amount']}")

    user = await get_user(message.from_user.id)
    wallet = await get_user_ton_wallet(user)

    if float(data['amount']) > float(await get_ton_wallet_balance(wallet)):
        await message.answer("Ваш баланс меньше введенного числа. Вывод невозможен")
        await state.finish()
    else:
        await message.answer("Подтвердите вывод: [yes/no]")
        await state.set_state(WithdrawState.waiting_for_confirmation_ton.state)

@dp.message_handler(state=WithdrawState.waiting_for_confirmation_ton.state)
async def process_ton_wallet_confirmation(message: types.Message, state: FSMContext):
    confirmation = message.text
    
    if confirmation.lower() != "yes":
        await message.answer("Транзакция отменена")
    else:

        user = await get_user(message.from_user.id)

        wallet = await get_user_ton_wallet(user)

        data = await state.get_data()

        ans = await send_ton_transaction(wallet=wallet, address=data["wallet_address"], amount=float(data["amount"]), message="Transaction from bot")

        await message.answer(ans)
        
        await state.finish()


@dp.message_handler(state=WithdrawState.bnb_process_beginning.state)
async def process_bnb_wallet_beginning(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)

    wallet = await get_user_bnb_wallet(user)
    await message.answer(f"Баланс кошелька BNB: {await get_bnb_wallet_balance(wallet)}", reply_markup=ReplyKeyboardRemove())
    await message.answer("Введите адрес вашего кошелька:")
    await state.set_state(WithdrawState.waiting_for_bnb_wallet_address.state)

# Обработчик ввода адреса кошелька
@dp.message_handler(state=WithdrawState.waiting_for_bnb_wallet_address.state)
async def process_bnb_wallet_address(message: types.Message, state: FSMContext):
    wallet_address = message.text
    await state.update_data(wallet_address = message.text)
    await message.answer(f"Вы ввели адрес кошелька: {wallet_address}.\nВведите количество в BNB")
    await state.set_state(WithdrawState.waiting_for_withdraw_bnb_amount.state)
    print("Установил состояние жду количество")


@dp.message_handler(state=WithdrawState.waiting_for_withdraw_bnb_amount.state)
async def process_bnb_wallet_amount(message: types.Message, state: FSMContext):
    amount = message.text
    await state.update_data(amount = message.text)

    data = await state.get_data()

    await message.answer(f"Вы ввели адрес кошелька: {data['wallet_address']}\nВывести следующее число BNB: {data['amount']}")

    user = await get_user(message.from_user.id)
    wallet = await get_user_bnb_wallet(user)

    if float(data['amount']) > float(await get_bnb_wallet_balance(wallet)):
        await message.answer("Ваш баланс меньше введенного числа. Вывод невозможен")
        await state.finish()
    else:
        await message.answer("Подтвердите вывод: [yes/no]")
        await state.set_state(WithdrawState.waiting_for_confirmation_bnb.state)

@dp.message_handler(state=WithdrawState.waiting_for_confirmation_bnb.state)
async def process_bnb_wallet_confirmation(message: types.Message, state: FSMContext):
    confirmation = message.text
    
    if confirmation.lower() != "yes":
        await message.answer("Транзакция отменена")
    else:

        user = await get_user(message.from_user.id)

        wallet = await get_user_bnb_wallet(user)

        data = await state.get_data()

        result = await send_bnb_transaction(wallet=wallet, address=data["wallet_address"], amount=float(data["amount"]), message="Transaction from bot")

        await message.answer(result)
        
        await state.finish()

if __name__ == '__main__':
    ex = executor.Executor(dp)
    ex.start_polling()