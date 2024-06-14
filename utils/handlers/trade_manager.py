from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.filters.callback_data import CallbackData
from bot.keyboards.menu_keyboard import manage_trade_keyboard, manage_single_trade_kb
from bot.db_client import db
from database.user_functions import get_user_by_chat_id
from database.trade_functions import get_trades_by_user_id, delete_trade_by_id, get_trade_by_id
from database.wallet_functions import get_active_network_wallet
from database.ca_functions import get_coin, get_coin_by_id
from aiogram.filters import StateFilter

from solders.pubkey import Pubkey

from bot.callback_factories.start_action import StartAction
from bot.callback_factories.trades_manage import TradeAction, PairViewAction
from bot.handlers.routers import start_menu
from aiogram import F
from bot.utils import get_trade_stats
from bot.keyboards.menu_keyboard import confirmation_keyboard, back_to_main_kb, trade_pair_list_keyboard
from bot.callback_factories.confirmation_action import ConfirmAction
from bot.db_client import db

from bot.utils.solana_trade_utils import solana_base

from bot.kb_texts.all_messages import get_trade_message, no_open_trades, trade_sell_conf, sell_all_conf, get_bonk_open_trade_message

import asyncio
from database.ca_functions import  get_coin, get_coin_by_id


import json

@start_menu.callback_query(PairViewAction.filter(F.name=="options"))
async def display_trade_view(query: types.CallbackQuery, callback_data: PairViewAction):
    user = await get_user_by_chat_id(query.from_user.id, db)
    trade_id = callback_data.trade_id
    trade = await get_trade_by_id(trade_id, db)
    await process_trade_view(user, trade, query)



@start_menu.callback_query(PairViewAction.filter(F.name=="prev_trade"))
async def display_prev_trade_view(query: types.CallbackQuery, callback_data: PairViewAction):
    user = await get_user_by_chat_id(query.from_user.id, db)
    
    trades = await get_trades_by_user_id(user.id, db, static=False)

    if len(trades)>1:

        trade_id = callback_data.trade_id
        index = None
        for i in trades:
            if int(trades[i].id)==int(trade_id):
                index = 1
                break
        if index:
            trade = trades[index-1]

        # trade = await get_trade_by_id(trade_id, db)
        await process_trade_view(user, trade, query)
    else:
        await query.answer(text="You only have one trade")



@start_menu.callback_query(PairViewAction.filter(F.name=="next_trade"))
async def display_next_trade_view(query: types.CallbackQuery, callback_data: PairViewAction):
    user = await get_user_by_chat_id(query.from_user.id, db)
    
    trades = await get_trades_by_user_id(user.id, db, static=False)
    if len(trades)>1:

        trade_id = callback_data.trade_id
        index = None
        for i in trades:
            if int(trades[i].id)==int(trade_id):
                index = 1
                break
        if index:
            trade = trades[index+1]

        # trade = await get_trade_by_id(trade_id, db)
        await process_trade_view(user, trade, query)
    else:
        await query.answer(text="You only have one trade")

async def process_trade_view(user, current_trade, query):
    await query.answer('Loading Your Trade... Please Wait.')
    # trades = await get_trades_by_user_id(user.id, db, static=trade.static_trade)
    dexx = solana_base
    
    coin = await get_coin((current_trade.token_address), db)
    poolKeys = json.loads(coin.pool_keys)

    coin = await get_coin((current_trade.token_address), db)
    

    if coin:
        pair_address = coin.lp_address
    
    kb_type = 'pairs' if current_trade.static_trade else 'trades'
    kb = manage_single_trade_kb(coin.id, coin.lp_address, current_trade)
    
    wallet = await get_active_network_wallet(user, current_trade.network, db)
    if wallet:
        solana_base.wallet = wallet.wallet_address
        balance = current_trade.token_qty
        sol_in = current_trade.amount 
        balance = solana_base.get_sol_balance(Pubkey.from_string(wallet.wallet_address))
        
        dex_data = solana_base.get_dexscreener_pair_detail(pair_address=coin.lp_address)
        token_balance = solana_base.get_token_balance_w_wallet(coin.contract_address, wallet.wallet_address)
        sol_out = solana_base.get_price_sol_out(pair_address=coin.lp_address, token_in=token_balance, pool_keys=poolKeys)
        pnl = (sol_out - sol_in)/sol_in
        # print(dex_data, pnl, sol_in, sol_out, coin, current_trade, balance, token_balance)
        text = get_bonk_open_trade_message(dex_data, pnl, sol_in, sol_out, coin, current_trade, balance, token_balance)
        # text = get_trade_message(current_trade, pnl, sol_in, sol_out, coin)
        await query.message.edit_text(text=text, reply_markup=kb, parse_mode='Markdown')
        await query.answer()
    await query.answer(text=no_open_trades)


@start_menu.callback_query(StartAction.filter(F.type=="manage_pairs"))
async def open_pairs_manager(query: types.CallbackQuery, callback_data: CallbackData):
    await query.answer('Loading Your Trades... Please Wait.')
    user = await get_user_by_chat_id(query.from_user.id, db)
    trades = await get_trades_by_user_id(user.id, db, static=True)
    found_pairs = []
    all_trades = []
    for trade in reversed(trades):
        if trade.coin_symbol not in found_pairs:
            found_pairs.append(trade.coin_symbol)
            all_trades.append(trade)
    kb = trade_pair_list_keyboard(user, all_trades)
    await query.message.edit_text(text="Please choose the pair!",reply_markup=kb)
    return
    


@start_menu.callback_query(StartAction.filter(F.type=="manage_trades"))
async def open_trades_manager(query: types.CallbackQuery, callback_data: CallbackData):
    await query.answer('Loading Your Trades... Please Wait.')
    user = await get_user_by_chat_id(query.from_user.id, db)
    trades = await get_trades_by_user_id(user.id, db, static=False)
    found_pairs = []
    all_trades = []
    for trade in reversed(trades):
        if trade.coin_symbol not in found_pairs:
            found_pairs.append(trade.coin_symbol)
            all_trades.append(trade)
    kb = trade_pair_list_keyboard(user, all_trades)
    await query.message.edit_text(text="Please choose the pair!",reply_markup=kb)
    return
    



@start_menu.callback_query(TradeAction.filter(F.value=="open_monitor"))
async def link_monitor(query: types.CallbackQuery, callback_data: TradeAction):
    
    coin_id = callback_data.trade_id
    coin = await get_coin_by_id(coin_id, db)

    user = await get_user_by_chat_id(query.from_user.id, db)
    trades = await get_trades_by_user_id(user.id, db, static=False)
    
    
    trades1 = [trade for trade in trades if trade.token_address.lower()==coin.contract_address.lower()]
    
    if not trades1:
        trades = await get_trades_by_user_id(user.id, db, static=True)
    
        trades1 = [trade for trade in trades if trade.token_address.lower()==coin.contract_address.lower()]
    
        if not trades1:
            await query.answer('You do not have an open trade for this coin.')
            return
    await process_trade_view(user, trades1[0], query)
    return
    
    

@start_menu.callback_query(TradeAction.filter(F.value=="sell_now"), StateFilter('*'))
async def switch_trade_cb2(query: types.CallbackQuery, callback_data: TradeAction, state: FSMContext):
    new_id = callback_data.trade_id
    kb = confirmation_keyboard('sell_trade')
    text = trade_sell_conf
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()
    await state.set_data({"id":new_id})
    

@start_menu.callback_query(TradeAction.filter(F.value=="sell_all"), StateFilter('*'))
async def sell_all_cb(query: types.CallbackQuery, callback_data: TradeAction, state: FSMContext):
    new_id = callback_data.trade_id
    kb = confirmation_keyboard('sell_all_trades')
    text = sell_all_conf
    await query.message.edit_text(text=text, reply_markup=kb, parse_mode='MarkDown')
    await query.answer()

    await state.set_data({"id":new_id})



@start_menu.callback_query(ConfirmAction.filter(F.action=="sell_all_trades"), StateFilter('*'))
async def sell_confirm_all(query: types.CallbackQuery, callback_data: ConfirmAction, state: FSMContext):
    resp = callback_data.value
    if resp == "confirm":
        data = await state.get_data()
        id = data['id']
        user = await get_user_by_chat_id(query.from_user.id, db)
        trades = await get_trades_by_user_id(user.id, db)
        eth_wallet = await get_active_network_wallet(user, "ethereum", db)
        sol_wallet = await get_active_network_wallet(user, "solana", db)
        
        # Notify the user that the process has been initiated
        await query.message.edit_text(text="❌ Sell action has been initiated. Please wait...")
        eth_trades = [trade for trade in trades if trade.network=="ethereum"]
        sol_trades = [trade for trade in trades if trade.network=="solana"]
        
        # Call sell_all function in a separate thread
        if eth_trades:
            sell_all_task = asyncio.create_task(get_trade_stats.sell_all(user, eth_trades, eth_wallet))
            await sell_all_task
        if sol_trades:
            sell_all_task = asyncio.create_task(get_trade_stats.sell_all(user, sol_trades, sol_wallet))
            await sell_all_task

        await query.message.answer(text=f"🎉 Sale completed successfully! 🎉\n",reply_markup=back_to_main_kb())
        
    else:
        await query.message.answer(text="❌ Sale action halted. No changes made. ❌",reply_markup=back_to_main_kb())



@start_menu.callback_query(ConfirmAction.filter(F.action=="sell_trade"), StateFilter('*'))
async def sell_confirm(query: types.CallbackQuery, callback_data: ConfirmAction, state: FSMContext):
    resp = callback_data.value
    if resp == "confirm":
        data = await state.get_data()
        id = data['id']
        user = await get_user_by_chat_id(query.from_user.id, db)
        list_i = await get_trade_by_id(data['id'], db)
        
        
        wallet = await get_active_network_wallet(user, list_i.network, db)
        print(f"Sell initiated by: {wallet.wallet_address} | Trade id: {list_i.id}")
        await query.message.edit_text(text="🔄 Processing your sale... Hang tight! 🕐")

        status, hex1 = await get_trade_stats.sell_trade(user, list_i, wallet)
        if status:
            await query.message.edit_text(text=f"✅ Sold!!.\nTransaction Hash: {hex1}",reply_markup=back_to_main_kb())
        else:
            await query.message.edit_text(text=f"❌ Error while selling.\n Error Message: {hex1}",reply_markup=back_to_main_kb())
        
    else:
        await query.message.edit_text(text="❌ Sell action has been cancelled.",reply_markup=back_to_main_kb())

@start_menu.callback_query(TradeAction.filter(F.value=="delete"), StateFilter('*'))
async def delete_trade(query: types.CallbackQuery, callback_data: ConfirmAction, state: FSMContext):
    new_id = callback_data.trade_id
    kb = confirmation_keyboard('delete_trade')
    text = "‼️ You sure you want to delete this trade? ‼️"
    await query.message.edit_text(text=text, reply_markup=kb)
    await query.answer()
    await state.set_data({"id":new_id})



@start_menu.callback_query(ConfirmAction.filter(F.action=="delete_trade"), StateFilter('*'))
async def delete_trade_confirm(query: types.CallbackQuery, callback_data: ConfirmAction, state: FSMContext):
    resp = callback_data.value
    if resp == "confirm":
        id = await state.get_data()
        trade = await delete_trade_by_id(id['id'], db)
        await query.answer(text="Trade has been deleted.")
        await open_trades_manager(query, callback_data)
    else:
        await query.answer(text="Alright! It's cancelled.")
        await open_trades_manager(query, callback_data)