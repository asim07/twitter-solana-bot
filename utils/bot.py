import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv
import os
from aiogram.fsm.context import FSMContext
from aiogram.enums.chat_type import ChatType


load_dotenv()

# Bot token can be obtained via https://t.me/BotFather
TOKEN = os.getenv('BOT_TOKEN')

#Bot instance as bot 
bot = Bot(TOKEN, parse_mode=ParseMode.HTML)

#dispatcher instace as dp
dp = Dispatcher()