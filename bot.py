# Aiogram imports
from aiogram import Bot, Dispatcher, types

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, \
                          InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import config

from web3 import Web3

from telegram import Update
from db import session, User

import ton



w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)




async def get_user(user_id):
    user = session.query(User).filter_by(user_id=user_id).first()
    if user is None:
        user = User(user_id=user_id, ton_balance=0, bnb_balance=0, lt_balance=0, risk_amount=0)
        session.add(user)
        session.commit()
    return user


@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    # user = await get_user(message.from_user.id)

    user = session.query(User).filter_by(user_id=message.from_user.id).first()
    if user is None:
        user = User(user_id=message.from_user.id, ton_balance=0, bnb_balance=0, lt_balance=0, risk_amount=0)
        session.add(user)
        session.commit()
        await bot.send_message(user.user_id, f"Вы зарегистрировались. Ваш пользователь выглядит так:\n{user.user_id}")
    else:
        await bot.send_message(user.user_id, f"Log IN. Ваш пользователь выглядит так:\n{user.user_id}")

    # await bot.send_message(user.user_id, f"Вы зарегистрировались. Ваш пользователь выглядит так:\n{user.user_id}")

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
    # Function that gives user the address to deposit

    uid = message.from_user.id

    # Keyboard with deposit URL
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton('Deposit',
                                #   url=f'ton://transfer/{config.DEPOSIT_ADDRESS}&text={uid}')
                                  url=f'ton://transfer/{config.DEPOSIT_ADDRESS}')
    keyboard.add(button)

    # Send text that explains how to make a deposit into bot to user
    await message.answer('It is very easy to top up your balance here.\n'
                         'Simply send any amount of TON to this address:\n\n'
                         f'`{config.DEPOSIT_ADDRESS}`\n\n'
                         f'And include the following comment: `{uid}`\n\n'
                         'You can also deposit by clicking the button below.',
                         reply_markup=keyboard)



if __name__ == '__main__':
    ex = executor.Executor(dp)
    ex.loop.create_task(ton.start())
    ex.start_polling()