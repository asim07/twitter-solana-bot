from bot.utils.ca_helpers import  process_solana_token
from aiogram import types


from bot.db_client import db
from aiogram.filters import StateFilter

from bot.keyboards.holdT_keyboard import holdT_menu_keyboard
from bot.keyboards.paid_user_kb import default_menu_keyboard
from bot.handlers.routers import ca_menu
from database.ca_functions import  get_coin
from database.user_functions import get_user_by_chat_id, update_user_holdT_status
from database.holding_token_functions import update_holding_amount
from database.ca_functions import add_sol_coin_data

from aiogram import F

from bot.utils.solana_trade_utils import solana_base

from bot.utils.config import HOLDING_TOKEN, HOLDING_AMOUNT
from bot.utils import sol_swaps
from bot.kb_texts.all_messages import holdT_base_message, hodlT_success_message, generate_deposit_message
from bot.callback_factories.hodlT_action import HoldTAction
import json

@ca_menu.callback_query(HoldTAction.filter(F.action=="buy"), StateFilter('*'))
async def hodlT_buy(query: types.CallbackQuery, state):
    await query.answer(text='Buy action is initiated.! Please wait for further result.')
    user = await get_user_by_chat_id(query.from_user.id, db)
    coin = await get_coin(HOLDING_TOKEN, db)
    if not coin:
        data = process_solana_token(HOLDING_TOKEN)
        coin = await add_sol_coin_data(data, db)
    price, _ = solana_base.get_price_sol_in(coin.lp_address, 1, json.loads(coin.pool_keys))
    sol_in = HOLDING_AMOUNT*1.02*(1/float(price))
    response = await sol_swaps.buy_for_user(user, coin, sol_in)
    if not response:
        await query.message.answer(text='Unable to buy the coin. Please report the issue to admin or deposit coins.')
        await query.message.delete()
        return
    await query.message.answer(text='Buy transaction has been submitted. Please wait for confirmation and hit refresh.')
    await query.message.delete()




@ca_menu.callback_query(HoldTAction.filter(F.action=="refresh"), StateFilter('*'))
async def hodlT_refresh(query: types.CallbackQuery, state):
    user = await get_user_by_chat_id(query.from_user.id, db)
    wallet = user.wallets[0].wallet_address
    balance = solana_base.get_token_balance_w_wallet(HOLDING_TOKEN, wallet)
    if balance>=HOLDING_AMOUNT:
        await update_holding_amount(user.id, float(balance), db)
        await update_user_holdT_status(user.chat_id, True, db)
        reply = hodlT_success_message(wallet, balance)
        await query.message.answer(text=reply, reply_markup=default_menu_keyboard(user), parse_mode="Markdown")
        await query.message.delete()
        return
    else:
        reply = holdT_base_message(wallet, balance)    
    await query.message.answer(text=reply, reply_markup=holdT_menu_keyboard(), parse_mode="Markdown")
    await query.message.delete()
    return



@ca_menu.callback_query(HoldTAction.filter(F.action=="deposit"), StateFilter('*'))
async def hodlT_buy(query: types.CallbackQuery, state):
    user = await get_user_by_chat_id(query.from_user.id, db)
    wallet = user.wallets[0].wallet_address
    reply = generate_deposit_message(wallet, HOLDING_TOKEN)
    await query.message.answer(text=reply, parse_mode='Markdown')
    

