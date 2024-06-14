from bot.utils.ca_helpers import  generate_message, fetch_token_info,  process_solana_token
from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.keyboards.ca_keyboards import buy_keyboard, sell_keyboard
from bot.db_client import db
from aiogram.filters import Command, StateFilter
from bot.utils.wallet_methods import eth_test_wm
from bot.callback_factories.start_action import StartAction
from bot.handlers.routers import ca_menu
from database.ca_functions import  update_coin_data, get_coin, get_coin_by_id, add_tracking,  get_single_tracking
from database.user_functions import get_user_by_chat_id
from database.wallet_functions import get_active_network_wallet
from database.ca_functions import add_sol_coin_data, delete_tracking
from database.trade_functions import store_active_trade, store_static_trade, delete_trade_by_id, update_trade_balance, get_trades_by_user_id, update_trade_amount, add_final_eth
from database.user_functions import change_network
from database.limit_orders_functions import add_limitorder_data
from bot.kb_texts.all_messages import get_bonk_pending_trade_message
from aiogram import F

from bot.utils.solana_trade_utils import SolanaUtils, solana_base

from bot.keyboards.menu_keyboard import single_trade_button

from bot.callback_factories.ca_action import BuyAction, SellAction
from bot.states.sniperBot import CAStates
import logging
from bot.utils  import get_trade_stats

from bot import app
from threading import Thread
import asyncio
from bot.utils.config import LAMPORTS_PER_SOL, SOL_FEE_WALLET, SOL_FEE, GROUP_CHAT_ID
from bot.utils import sol_swaps

from solders.pubkey import Pubkey
from solders.keypair import Keypair


logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
logger.addHandler(handler)


def track_pending_tx(tx_hash, user, direction, w3, network, base,  coin, amount, out_qty, event_loop):
    tx_hash_ = tx_hash

    etherscan_url = f"https://solscan.io/tx/{tx_hash}"


    message = f"✅ {direction.title()} transaction has been successful!. [View on Blockscan]({etherscan_url})"
        
    asyncio.run(app.bot.send_message(chat_id=user.chat_id, text=message, parse_mode='Markdown', disable_web_page_preview=True))
    return

async def auto_approve(base,  network, user, coin, amount, tx_hash_, out_qty, direction, eth_out=0):
    if direction.lower()=="sell":
        trades = await get_trades_by_user_id(user.id, db, static=False)
        trades = [trade for trade in trades if trade.token_address.lower()==coin.contract_address.lower()]
        if trades:
            if int(trades[0].token_qty)==int(amount):
                await delete_trade_by_id(trades[0].id, db)
            else:
                await update_trade_balance(trades[0],int(trades[0].token_qty)-int(amount),db)
                await update_trade_amount(trades[0],int(trades[0].amount)-int(out_qty),db)
        else:
            print('Trade was not found.')
        
        
        return
    token_balance = base.get_token_balance(coin.contract_address)
    
    await store_active_trade(user.id, network, coin.contract_address, coin.quote_address, tx_hash_, direction.lower(), amount, coin.name, coin.symbol, coin.dex, out_qty, token_balance, db)
    
    return

def generate_trade_notification(coin_symbol: str, direction: str, amount: float, tx_signature: str) -> str:
    """
    Generates a well-formatted trade notification message.

    Parameters:
    - coin_symbol (str): The symbol of the coin (e.g., BTC, ETH).
    - direction (str): The direction of the trade (Buy or Sell).
    - amount (float): The amount of the coin being traded.
    - tx_signature (str): The signature of the transaction.

    Returns:
    - str: A formatted message for a trade notification.
    """
    
    # Header
    message_header = "🔔 Trade Notification 🔔"
    
    # Trade details
    trade_details = f"""
📈 *Trade Details:*
- **Coin:** {coin_symbol}
- **Direction:** {direction}
- **Amount:** {amount}
    """
    
    # Transaction signature
    tx_info = f"🔏 *Transaction Signature:*\n`{tx_signature}`"
    
    # Combine all parts
    complete_message = f"{message_header}\n{trade_details}\n{tx_info}"
    
    return complete_message


async def transfer_fee(base, network, user, coin, amount, tx_hash_, out_qty, direction, eth_out=0, order_data={}):
    # fee = base.transfer_sol(to=SOL_FEE_WALLET, amount=amount*0.02)
    if direction.lower()=="sell":
        trades = await get_trades_by_user_id(user.id, db, static=False)
        trades = [trade for trade in trades if trade.token_address.lower()==coin.contract_address.lower()]
        if trades:
            if int(trades[0].token_qty)==int(amount):
                await delete_trade_by_id(trades[0].id, db)
            else:
                await update_trade_balance(trades[0],int(trades[0].token_qty)-int(amount),db)
                await update_trade_amount(trades[0],int(trades[0].amount)-int(out_qty),db)
            await add_final_eth(trades[0], eth_out, db)
        else:
            print('Trade was not found.')
        
        return
    # status, hash1 = base.approve(token_address=coin.contract_address, amount=amount)
    
    token_balance = base.get_token_balance(coin.contract_address)
    
    trade = await store_active_trade(user.id, network, coin.contract_address, coin.quote_address, str(tx_hash_), direction.lower(), amount, coin.name, coin.symbol, coin.dex, out_qty, token_balance, db)
    if direction.lower()=="buy":
        await add_limitorder_data(order_data, db)
    # channel_message = generate_trade_notification(coin.symbol, direction, amount, tx_hash_)
    # try:
    #     await app.bot.send_message(chat_id=GROUP_CHAT_ID, message_thread_id=4, text=channel_message)
    # except:
    #     print('Error while sending to channel')
    await app.bot.send_message(chat_id=user.chat_id, text=f"✅ {direction.title()} Trade is registered {coin.symbol}!", reply_markup=single_trade_button(trade))
    return


async def register_buy(user, coin, amount, tx_hash_):
    network = "solana"
    direction = "buy"
    # fee = base.transfer_sol(to=SOL_FEE_WALLET, amount=amount*0.02)
    wallet = await get_active_network_wallet(user, 'solana', db)
    token_balance = solana_base.get_token_balance_w_wallet(coin.contract_address, wallet.wallet_address)
    
    trade = await store_active_trade(user.id, network, coin.contract_address, coin.quote_address, str(tx_hash_), direction.lower(), amount, coin.name, coin.symbol, coin.dex, token_balance, token_balance, db)
    await app.bot.send_message(chat_id=user.chat_id, text=f"✅ {direction.title()} Trade is registered {coin.symbol}!", reply_markup=single_trade_button(trade))
    return




@ca_menu.callback_query(StartAction.filter(F.type=="start_sniping"), StateFilter('*'))
async def ask_for_ca(query: types.CallbackQuery, callback_data: StartAction, state: FSMContext):
    await query.answer(text="Please reply with contract address of the token you want to snipe.")
    return

@ca_menu.message(StateFilter(None))
async def ca_main_cb(message: types.Message):
    if message.text:
        if len(message.text)==44 or len(message.text)==43:
            ca = message.text
            coin = await get_coin(ca, db)
            # logger.info(f"At the start: {coin}")
            await message.answer(text=f"Coin is loading...") 
            if coin:
                # if coin.pair_created_at:
                data = fetch_token_info(ca)
                
                if data:
                    coin.price = data['price']
                    coin.price_usd = data['price_usd']
                    coin.liquidity = data['liquidity']
                    coin.market_cap = data['market_cap']
                    await update_coin_data(coin, db)
                else:
                    data = process_solana_token(ca)               

            else:
                data = process_solana_token(ca)
            coin = await add_sol_coin_data(data, db)
            # coin_data = coin.to_dict()
            # del coin_data['id']
            # coin = await update_coin_data(coin_data, db)
            

            # coin = await get_coin(ca,db)
            network = coin.network
            user = await get_user_by_chat_id(message.from_user.id, db)
            if coin.network.lower()!=user.active_network.lower():
                user = await change_network(coin.network, user.id, db)
            
            
            wallet = await get_active_network_wallet(user, user.active_network, db)
            if wallet:
                balance = get_token_balance(user, coin, wallet)
                print(balance)
                sol_balance = solana_base.get_sol_balance(Pubkey.from_string(wallet.wallet_address))
            else:
                balance = 0
            tracking = True if await get_single_tracking(coin, user, db) else False
            if coin.lp_address:
                dex_data = solana_base.get_dexscreener_pair_detail(coin.lp_address)
                out_message = get_bonk_pending_trade_message(dex_data, coin, balance, sol_balance)
            else:
                out_message = generate_message(coin, tracking, balance)
            await message.reply(text=out_message, reply_markup=buy_keyboard(user, network, coin.id, coin.lp_address, tracking),parse_mode='Markdown', disable_web_page_preview=True)

def get_token_balance(user, coin, wallet):
    if user.active_network.lower()=="solana":
        solana_base.keypair = Keypair.from_base58_string(eth_test_wm.decrypt_seed(wallet.wallet_encrypted_seed)) 
        balance = solana_base.get_token_balance(coin.contract_address)
        
    return balance


@ca_menu.message(StateFilter("prelaunch_buy_amount"))
async def auto_snipe_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    coin = data['coin']
    amount = message.text
    try:
        amount = float(amount.strip())
        await state.set_state(None)
    except:
        await message.reply('Please provide correct amount in numbers etc 0.2 1.4 etc')
        return
    user = await get_user_by_chat_id(message.from_user.id, db)
    tracking = await add_tracking(coin, user, amount, db)
    wallet = await get_active_network_wallet(user, coin.network, db)
    
    if wallet:
        balance = get_token_balance(user, coin, wallet)
    else:
        balance = 0
    await message.answer(text="Snipe order has been placed!")
    out_message = generate_message(coin, tracking.active, balance)
    await message.edit_text(text=out_message,parse_mode='Markdown',reply_markup=buy_keyboard(user, coin.network,coin.id,coin.lp_address, tracking.active), disable_web_page_preview=True)
    return

@ca_menu.callback_query(BuyAction.filter(F.amount.func(lambda amount: len(amount)>0)))
async def handle_buy_click(query: types.CallbackQuery, callback_data: BuyAction, state, ape_max=False):
    amount = callback_data.amount
    network = callback_data.network
    coin_id = callback_data.coin
    user = await get_user_by_chat_id(query.from_user.id, db)
    wallet = await get_active_network_wallet(user, network, db)
    coin = await get_coin_by_id(coin_id, db)
    if wallet:
        balance = get_token_balance(user, coin, wallet)
    else:
        balance = 0
    await query.answer(text="Processing the command, please wait.")
    if callback_data.prelaunch:
        if callback_data.amount=='refresh':
            wallet = await get_active_network_wallet(user, user.active_network, db)
            if wallet:
                balance = get_token_balance(user, coin, wallet)
                sol_balance = solana_base.get_sol_balance(Pubkey.from_string(wallet.wallet_address))
            else:
                balance = 0
            tracking = True if await get_single_tracking(coin, user, db) else False
            if coin.lp_address:
                dex_data = solana_base.get_dexscreener_pair_detail(coin.lp_address)
                out_message = get_bonk_pending_trade_message(dex_data, coin, balance, sol_balance)
            else:
                out_message = generate_message(coin, tracking, balance)
            await query.message.reply(text=out_message, reply_markup=buy_keyboard(user, network, coin.id, coin.lp_address, tracking),parse_mode='Markdown', disable_web_page_preview=True)
            return

        elif callback_data.amount=="X":
            await query.message.reply(text="Please provide the amount you want to use for snipe: ", reply_markup=types.ForceReply())
            await state.set_data(data={'coin':coin})
            await state.set_state('prelaunch_buy_amount')
            return
        elif callback_data.amount=="max":
            if coin.network=="solana":
                amount = solana_base.get_sol_balance(wallet=Pubkey.from_string(wallet.wallet_address))
            else:
                amount = balance
        else:
            amount = float(callback_data.amount)
        tracking = await add_tracking(coin=coin,user=user, amount=amount, db=db)
        await query.message.answer(text="Snipe order has been placed!")
        out_message = generate_message(coin, tracking.active, balance)
        await query.message.edit_text(text=out_message,parse_mode='Markdown',reply_markup=buy_keyboard(user, network,coin.id,coin.lp_address, tracking.active), disable_web_page_preview=True)
        return
    
    
    if callback_data.amount=='refresh':
        wallet = await get_active_network_wallet(user, user.active_network, db)
        if wallet:
            balance = get_token_balance(user, coin, wallet)
            sol_balance = solana_base.get_sol_balance(Pubkey.from_string(wallet.wallet_address))
        else:
            balance = 0
        tracking = True if await get_single_tracking(coin, user, db) else False
        if coin.lp_address:
            dex_data = solana_base.get_dexscreener_pair_detail(coin.lp_address)
            out_message = get_bonk_pending_trade_message(dex_data, coin, balance, sol_balance)
        else:
            out_message = generate_message(coin, tracking, balance)
        await query.message.edit_text(text=out_message, reply_markup=buy_keyboard(user, network, coin.id, coin.lp_address, tracking),parse_mode='Markdown', disable_web_page_preview=True)
        return
    
    if callback_data.amount=="switch":
        tracking = True if await get_single_tracking(coin, user, db) else False
        await query.message.edit_reply_markup(reply_markup=sell_keyboard(user, network,coin.id, coin.lp_address, tracking))
        return
    
    if callback_data.amount=="track":
        tracking = await get_single_tracking(coin, user, db)
        if tracking:
            resp = await delete_tracking(coin, user, db)
            if resp:
                await query.answer("Snipe order is deleted")
            else:
                await query.answer("No sniper order found.")
            out_message = generate_message(coin, False, balance)
            await query.message.edit_text(text=out_message,parse_mode='Markdown',reply_markup=buy_keyboard(user, network,coin.id,coin.lp_address, False), disable_web_page_preview=True)
            
            return
        else:
            await query.answer(text="Please click amount you want to use for sniping this token on launch.")
            return
        # tracking = await add_tracking(coin=coin,user=user, db=db)
        
        # out_message = generate_message(coin, tracking.active, balance)
        # await query.message.edit_text(text=out_message,parse_mode='Markdown',reply_markup=buy_keyboard(user, network,coin.id,coin.lp_address, tracking.active), disable_web_page_preview=True)
        # return

    if callback_data.amount=="monitor":
        price_in = get_trade_stats.get_pair_price(coin.contract_address, coin.quote_address, dex=coin.dex)
        # print(coin.name, coin.contract_address, coin.quote_address, coin.dex)
        resp = await store_static_trade(user.id, network, coin.contract_address, coin.quote_address, "", 'buy', balance, coin.name, coin.symbol, coin.dex.replace("_",""), price_in, balance, db)
        
        if resp:

        # tracking = await add_tracking(coin=coin,user=user, db=db)
        
        # out_message = generate_message(coin, tracking.active, balance)
        # await query.message.edit_text(text=out_message,parse_mode='Markdown',reply_markup=buy_keyboard(user, network,coin.id,coin.lp_address))
            await query.answer('You are monitoring this coin now. Check active trades section')
        else:
            await query.answer('Already monitoring this pair.')
        return

    await query.answer()
    if not wallet:
        await query.message.reply(text=f"You do not have any active wallet for {network} network.")
        return
    

   
    base = solana_base
    base.keypair = Keypair.from_base58_string(eth_test_wm.decrypt_seed(wallet.wallet_encrypted_seed))
    base.token_address = coin.contract_address
    balance = base.get_sol_balance(base.keypair.pubkey())
    
    
    all_in = False
    if balance>0:
        if amount == "max":
            amount = balance
            all_in = True
        elif amount == "X":
            data = {"coin":coin, "base":base,"user":user,"wallet":wallet}
            await state.set_data(data)
            await state.set_state(CAStates.buyX)
            await query.message.reply(text=f"Please reply with amount you want to spend to buy this token:",reply_markup=types.ForceReply(input_field_placeholder="0.05"))
            return
        else:
            amount = float(amount)
        await query.answer()        
        await sol_swaps.buy_for_user(user, coin, amount)
    else:
        await query.message.reply(text=f"Your account balance is zero.")
        query.answer()
        return
        
    

@ca_menu.message(StateFilter(CAStates.buyX))
async def get_x_amount(message: types.Message, state):
    amount = message.text
    
    try:
        amount = float(amount)
        data = await state.get_data()
        coin = data['coin']
        wallet = data['wallet']
        user = data['user']
        base = data['base']
        network = coin.network
        
        
        await sol_swaps.buy_for_user(user, coin, amount)
    except Exception as e:
        print(e)
        logger.error(e)
        await message.reply(text=f"Error: {e}")
    await state.clear()


@ca_menu.callback_query(SellAction.filter(F.amount.func(lambda amount: len(amount)>0)))
async def handle_sell_click(query: types.CallbackQuery, callback_data: SellAction, state):
    amount = callback_data.amount
    network = callback_data.network
    
    coin_id = callback_data.coin
    coin = await get_coin_by_id(coin_id, db)
    user = await get_user_by_chat_id(query.from_user.id, db)
    await query.answer(text="Processing the command, please wait.")
    if callback_data.amount=="switch":
        tracking = True if await get_single_tracking(coin, user, db) else False
        await query.message.edit_reply_markup(reply_markup=buy_keyboard(user, network,coin.id, coin.lp_address, tracking))
        return
    

    if callback_data.amount=="track":
        tracking = await add_tracking(coin=coin,user=user, db=db)
        await query.answer(text="We are looking out for this coin now for you!")
        return

    
    wallet = await get_active_network_wallet(user, network, db)
    if not wallet:
        await query.message.reply(text=f"You do not have any active wallet for {network} network.")
        return
    
    if amount == "100":
        all_in = True
    elif amount == "sell_x":
        await query.message.reply(text=f"Please specify the amount you'd like to allocate for selling this token:",reply_markup=types.ForceReply(input_field_placeholder="0.05"))
        data = {"coin":coin, "base":solana_base,"user":user,"wallet":wallet}
        await state.set_data(data)
        await state.set_state(CAStates.sellX)
        # await get_xx_amount(query.message, state)
        return
    
    await sol_swaps.sell_for_user(user, coin, amount, percentage=True)

@ca_menu.message(StateFilter(CAStates.sellX))
async def get_xx_amount(message: types.Message, state):
    amount = message.text
    try:
        amount = float(amount)
        if amount>100:
            await message.reply('Cannot sell more than 100%. Please enter again.',reply_markup=types.ForceReply(input_field_placeholder=65))
            return
        data = await state.get_data()
        coin = data['coin']
        wallet = data['wallet']
        network = coin.network
        user = data['user']
        base = data['base']
        
        await sol_swaps.sell_for_user(user, coin, amount, percentage=True)
        
    except Exception as e:
        print(e)
        logger.error(e)
        await message.reply(text=f"Error: {e}")
    await state.clear()

