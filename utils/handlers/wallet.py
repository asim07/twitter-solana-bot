from solders.keypair import Keypair
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from database.user_settings_functions import add_user_settings
from bot.utils.config import default_sol_settings
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from bot.states.sniperBot import WalletState
from bot.callback_factories.wallet import WalletAction
from bot.callback_factories.start_action import StartAction
from bot.db_client import db
from database.user_functions import change_network
from bot.keyboards.menu_keyboard import wallet_manager_keyboard, delete_wallet_keyboard, back_to_main_kb, start_to_main_kb
from bot.handlers.routers import wallet_menu
from database.wallet_functions import user_has_wallet, add_wallet, get_active_wallets, change_active_wallet, view_wallets, delete_wallet_by_name, get_wallet_by_id
from database.user_functions import get_user_by_chat_id

from aiogram import F
from bot.kb_texts.all_messages import get_new_wallet_mesg
from bot.utils.solana_trade_utils import solana_base
from bot.utils.wallet_methods import eth_test_wm, send_wallet_info_message

import re, asyncio,logging

logger = logging.getLogger(__name__)
logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )


@wallet_menu.callback_query(StartAction.filter(F.type=="wallets"), StateFilter("*"))
async def new_user_wallet_cb(query: CallbackQuery, callback_data: dict, state: FSMContext):
    has_wallets = await user_has_wallet(query.from_user, db)
    user_data = await get_user_by_chat_id(query.from_user.id, db)
    kb = wallet_manager_keyboard(user_data, has_wallets)
    wallets = await get_active_wallets(query.from_user, db)
    wallets = [
        {
            'network': wallet.network,
            'name': wallet.name,
            'address': wallet.wallet_address,
        }
        for wallet in wallets
    ]
    wallet_message = send_wallet_info_message(wallets)
    await query.message.edit_text(wallet_message, reply_markup=kb, parse_mode='MarkDown')
    

@wallet_menu.message(StateFilter("*"), Command(commands=["wallet", "wallets"]))
async def new_user_wallet_cb1(message: types.Message, state: FSMContext):
    query = message
    has_wallets = await user_has_wallet(query.from_user, db)
    user_data = await get_user_by_chat_id(query.from_user.id, db)
    kb = wallet_manager_keyboard(user_data, has_wallets)
    wallets = await get_active_wallets(query.from_user, db)
    wallets = [
        {
            'network': wallet.network,
            'name': wallet.name,
            'address': wallet.wallet_address,
        }
        for wallet in wallets
    ]
    wallet_message = send_wallet_info_message(wallets)
    await query.answer(wallet_message, reply_markup=kb, parse_mode='MarkDown')

async def ask_for_wallet_address(query: types.CallbackQuery, state: FSMContext, network):
    await query.message.reply("Please enter your wallet private key:",reply_markup=ForceReply(input_field_placeholder="...."))
    data = {}    
    user =  await get_user_by_chat_id(query.from_user.id,db)
    data['network'] = user.active_network
    await state.set_data(data)
    await state.set_state(WalletState.connect_wallet)
    await query.message.delete()
    


@wallet_menu.callback_query(WalletAction.filter(F.type=="generate"))
async def generate_new_wallet_callback(query: types.CallbackQuery, state: FSMContext, callback_data):
    user =  await get_user_by_chat_id(query.from_user.id,db)
    network = user.active_network
    wallet_data = {}

    wallet_name = "SOL"
    seed, private, wallet = eth_test_wm.generate_sol_wallet()
    wallet_data['encrypted_seed'] = eth_test_wm.encrypt_seed(private)
    wallet_data['address'] = wallet
    wallet_data['network'] = network
    wallet_data['name'] = wallet_name
    
    await add_wallet(query.from_user.id, wallet_data, db)
    settings_data = default_sol_settings
    await add_user_settings(query.from_user, settings_data, db)
    message = get_new_wallet_mesg(wallet_name, network, wallet, private, seed)
    kb = start_to_main_kb()
    
    await query.message.answer(text=message, reply_markup=kb, parse_mode="MARKDOWN")
    await query.message.delete()
    await state.set_state(None)

@wallet_menu.callback_query(WalletAction.filter(F.type=="connect"))
async def connect_existing_wallet_callback(query: types.CallbackQuery, state: FSMContext, callback_data):
    user =  await get_user_by_chat_id(query.from_user.id, db)
    network = user.active_network
    wallet_name = "SOL"
    
    await state.set_data({'wallet_name':wallet_name})
    await ask_for_wallet_address(query, state, network)

@wallet_menu.message(StateFilter(WalletState.connect_wallet))
async def connect_existing_wallet_callback2(message: types.Message, state: FSMContext):
    
    user =  await get_user_by_chat_id(message.from_user.id,db)
    network = user.active_network
    address = message.text
    try:
        if network=="solana":
            name = "SOL"
            wallet_add = eth_test_wm.get_sol_address(address)
            if not re.match(r"^[1-9A-HJ-NP-Za-km-z]{87,88}$", address):
                await message.reply("🔑 Oops! That doesn't seem right. Please double-check and enter a valid Solana private key. 👀",reply_markup=back_to_main_kb())
                await state.set_state(None)
                return


        if address.startswith("0x"):
            address = address[2:]
        wallet_data = {}
        
        
        wallet_data['encrypted_seed'] = eth_test_wm.encrypt_seed(address)
        wallet_data['name'] = name
        wallet_data['address'] = wallet_add
        wallet_data['network'] = network
        
        await add_wallet(message.from_user.id, wallet_data, db)

        settings_data = default_sol_settings


        await add_user_settings(message.from_user, settings_data, db)
        
        status = ""
        
        response = f'''🔐 **Wallet Update Alert!**

    📛 **Name**: {wallet_data['address']}
    🌐 **Chain**: {network}
    📬 **Address**: `{wallet_data['address']}`

    {status} 🚀'''
        await message.answer(response,parse_mode="MARKDOWN",reply_markup=back_to_main_kb())
        await state.set_state(None)

    except Exception as e:
        print(f"Error while creating wallet from private key: {e}")
        await state.set_state(None)

@wallet_menu.callback_query(WalletAction.filter(F.type=="delete"), StateFilter("*"))
async def handle_delete_wallet(query: types.CallbackQuery, callback_data, state):
    kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🟢 Proceed ✅", callback_data=WalletAction(type="delete_wallet", value="confirm").pack()),
        InlineKeyboardButton(text="🔴 Abort ❌", callback_data=WalletAction(type="delete_wallet", value="cancel").pack())
    ]
    ])

    await query.message.edit_text(f"✨Are you sure you want to delete the wallet?", reply_markup=kb)
    await state.set_state("delete_wallet")



async def get_user_wallets(chat_id, network):
    user_data = await get_user_by_chat_id(chat_id, db)
    return [x for x in user_data.wallets if x.network.lower()==network.lower()]



async def ask_wallet_to_withdraw(message: types.Message, state: FSMContext, wallets):
    kb = delete_wallet_keyboard(wallets)
    data = await state.get_data()
    await message.answer("Please select the wallet from which you want to withdraw:", reply_markup=kb)
    await state.set_data(data)
    await state.set_state("withdraw_wallet_confirmation")

@wallet_menu.callback_query(StateFilter("delete_wallet_confirmation"))
async def delete_wallet_confirm_callback_handler(query: types.CallbackQuery, callback_data: WalletAction, state: FSMContext):

    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Proceed ✅", callback_data=WalletAction(type="delete_wallet", value="confirm").pack()),
            InlineKeyboardButton(text="🔴 Abort ❌", callback_data=WalletAction(type="delete_wallet", value="cancel").pack())
        ]
    ])

    await query.message.edit_text(f"✨Are you sure you want to delete the wallet?", reply_markup=kb)
    await state.set_state("delete_wallet")

@wallet_menu.callback_query(StateFilter("delete_wallet"),WalletAction.filter(F.type=="delete_wallet"))
async def delete_wallet_callback_handler(query: types.CallbackQuery, callback_data: WalletAction, state: FSMContext):
    
    
    user =  await get_user_by_chat_id(query.from_user.id,db)
    network = user.active_network
    wallet_name = "ETH" if network=="ethereum" else "SOL"
    if callback_data.value == "confirm":
        await delete_wallet_by_name(wallet_name,query.from_user, network, db)
        user =  await get_user_by_chat_id(query.from_user.id,db)
        wallets = [x for x in user.wallets]
        if wallets:
            await change_network(wallets[0].network, user.id, db)
        if wallet_name != "Main":
            message = f"Wallet '{wallet_name}' has been deleted."
        else:
            message = f"Wallet has been deleted!"
        await query.message.edit_text(message,reply_markup=back_to_main_kb())
    else:
        await query.message.edit_text("Wallet deletion canceled.",reply_markup=back_to_main_kb())

    # await state.reset_state()
    await state.set_state(None)



@wallet_menu.callback_query(WalletAction.filter(F.type=="private_key"))
async def handle_disp_priv_key(query: types.CallbackQuery, state: FSMContext, callback_data):
    
    data = {}
    user =  await get_user_by_chat_id(query.from_user.id,db)
    network = user.active_network
    data['network'] = network
    wallets = await get_user_wallets(query.from_user.id, network)
    wallet = wallets[0]
    private_key = eth_test_wm.decrypt_seed(wallet.wallet_encrypted_seed)
    wallet_address = wallet.wallet_address
    response = f'''*Wallet:* `{wallet_address}`\n\n*Private Key:* `{private_key}`'''
    await query.message.reply(text=response, parse_mode='MarkDown')


@wallet_menu.callback_query(WalletAction.filter(F.type=="withdraw"))
async def handle_delete_wallet(query: types.CallbackQuery, state: FSMContext, callback_data):
    
    data = {}
    user =  await get_user_by_chat_id(query.from_user.id,db)
    network = user.active_network
    data['network'] = network
    wallets = await get_user_wallets(query.from_user.id, network)
    wallet = wallets[0]
    wallet_id = wallet.id
    
    
    await state.update_data(wallet_id_to_withdraw=wallet_id)
    await state.update_data(network=network)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ I am sure!", callback_data=WalletAction(type="withdraw_wallet", value="confirm").pack()),
            InlineKeyboardButton(text="❌ Cancel", callback_data=WalletAction(type="withdraw_wallet", value="cancel").pack())
        ]
    ])

    await query.message.reply(f"✨Are you sure you want to withdraw wallet?", reply_markup=kb)
    await state.set_state("withdraw_wallet")




@wallet_menu.callback_query(StateFilter("withdraw_wallet"), WalletAction.filter(F.type=="withdraw_wallet"))
async def wt_wallet_callback_handler(query: types.CallbackQuery, callback_data: WalletAction, state: FSMContext):
    
    if callback_data.value == "confirm":
        mess = "📤 Please input the destination wallet address for the transfer. Where should we send it? 📍"
        await query.message.reply(text=mess, reply_markup=ForceReply(input_field_placeholder="...."))
        await state.set_state('receive_wallet_address')
        return
        
    else:
        await query.message.edit_text("Withdrawl process cancelled.",reply_markup=back_to_main_kb())

    # await state.reset_state()
    await state.set_state(None)

def is_valid_eth_address(address):
    if not isinstance(address, str):
        return False
    return address.startswith("0x") and len(address) == 42

@wallet_menu.message(StateFilter("receive_wallet_address"))
async def finally_send_it(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    wallet_id = user_data.get("wallet_id_to_withdraw")
    wallet = await get_wallet_by_id(wallet_id, db)
    
    private_key = eth_test_wm.decrypt_seed(wallet.wallet_encrypted_seed)
    
    solana_base.keypair = Keypair.from_base58_string(private_key)
    solana_base.wallet = solana_base.keypair.pubkey()
    balance = solana_base.get_sol_balance()
    sig = solana_base.transfer_sol(to=message.text, amount=balance)
    await message.reply(f"Tx has been sent: `{str(sig)}`", parse_mode="MarkDown")
    await state.set_state(None)
    return
    





