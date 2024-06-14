from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ForceReply
from aiogram.filters import Command
import re

from bot.keyboards.settings_keyboard import user_settings_keyboard 
from bot.keyboards.paid_user_kb import settings_zone_keyboard, default_menu_keyboard


from bot.states.sniperBot import UserSettingsState
from aiogram.types import  CallbackQuery

from bot.db_client import db
from aiogram.filters.callback_data import CallbackData
from database.user_functions import get_user_by_chat_id, toggle_user_active, change_network
from database.user_settings_functions import get_user_settings, set_user_setting, add_user_settings

from aiogram.filters import StateFilter
from bot.utils.config import  default_sol_settings
from bot.callback_factories.start_action import StartAction
from bot.callback_factories.user_settings_action import UserSettingsAction

from aiogram import F
from bot.db_client import db
from aiogram.utils.keyboard import InlineKeyboardBuilder 

from bot.keyboards.menu_keyboard import ask_for_network, back_to_main_kb
from bot.handlers.routers import user_settings_menu
from bot.kb_texts.all_messages import get_settings_message




@user_settings_menu.callback_query(StartAction.filter(F.type=="bot_active"), StateFilter("*"))
async def bot_active_cb(query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    user = await get_user_by_chat_id(query.from_user.id, db)
    await toggle_user_active(user.id, db)
    user.is_active = not user.is_active
    kb = default_menu_keyboard(user)
    try:
        await query.message.edit_reply_markup(reply_markup=kb)
    except:
        message = "Bot state changed, may be due to restart on backend. Please go to main menu to proceed."
        await query.message.edit_text(text=message,reply_markup=back_to_main_kb())




# @wallet_menu.callback_query(StartAction.filter(F.type=="wallets"), StateFilter("*"))
@user_settings_menu.callback_query(StartAction.filter(F.type=="user_settings"))
async def bot_network_settings(query: types.CallbackQuery, callback_data: dict):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = default_sol_settings
        setting = await add_user_settings(query.from_user, setting, db )
       
    message = get_settings_message(setting)
    await query.message.edit_text(text=message, reply_markup=user_settings_keyboard(network=setting.network), parse_mode="Markdown")

async def add_new_settings(query):
    user  = await get_user_by_chat_id(query.from_user.id, db)


    setting = default_sol_settings

    setting = await add_user_settings(query.from_user, setting, db )
    return setting

@user_settings_menu.message(Command(commands=['settings']))
async def bot_network_settings1(message: types.Message):
    query = message
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
       
    message1 = get_settings_message(setting)
    await query.reply(text=message1, reply_markup=user_settings_keyboard(network=setting.network), parse_mode="Markdown")

@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="amount_per_snipe"), StateFilter("*"))
async def amount_per_snipe_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id, db)
    if not setting:
        setting = await add_new_settings(query)

    unit = "SOL"
    message = f"Please enter the amount of {unit} you'd like to allocate for each new listing snipe:"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="0.01"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.sniper_amount)


@user_settings_menu.message(StateFilter(UserSettingsState.sniper_amount))
async def amount_per_snipe(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = float(messag)
        setting = await state.get_data()
        setting = setting['setting']
        setting.amount_per_snipe = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode="Markdown")
        await state.clear()
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 0.01, 0.1 etc")
        await state.clear()


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="auto_buy"), StateFilter("*"))
async def auto_buy_cb11(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    setting.auto_buy = not setting.auto_buy
    new_settings = await set_user_setting(setting, db)
    text1 = get_settings_message(new_settings)
    await query.message.edit_text(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode="Markdown")
    await query.answer(text="Auto Buy Setting changed!")


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="honeypot_settings"), StateFilter("*"))
async def hp_toggle_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    setting.hp_toggle = not setting.hp_toggle if setting.hp_toggle is not None else True
    new_settings = await set_user_setting(setting, db)
    text1 = get_settings_message(new_settings)
    await query.message.edit_text(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode="Markdown")
    await query.answer(text="Scam Detection Settings changed!")


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="auto_sell"), StateFilter("*"))
async def auto_sell_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    setting.auto_sell = not setting.auto_sell
    new_settings = await set_user_setting(setting, db)
    text1 = get_settings_message(new_settings)
    await query.message.edit_text(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode = "MarkDown")
    await query.answer(text="Auto Sell Setting changed!")


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="duplicate_buy"), StateFilter("*"))
async def duplicate_buy_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    setting.duplicate_buy = not setting.duplicate_buy
    new_settings = await set_user_setting(setting, db)
    text1 = get_settings_message(new_settings)
    await query.message.edit_text(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode = "MarkDown")
    await query.answer(text="Repeat Buy Setting changed!")


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="auto_sell_tp"), StateFilter("*"))
async def auto_sell_tp_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    message = "Please reply with take profit percentage e.g. 100?"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="100"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_tp)



@user_settings_menu.message(StateFilter(UserSettingsState.set_tp))
async def auto_sell_tp(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = float(messag)
        setting = await state.get_data()
        setting = setting['setting']
        setting.auto_sell_tp = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode = "MarkDown")
        await state.clear()
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
        await state.clear()






@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="auto_sell_sl"), StateFilter("*"))
async def set_sl_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    message = "Please reply with stop loss percentage e.g. 10?"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="10"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_sl)



@user_settings_menu.message(StateFilter(UserSettingsState.set_sl))
async def auto_sell_sl(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.auto_sell_sl = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode = "MarkDown")
        await state.clear()
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
        await state.clear()








@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="max_gas_price"), StateFilter("*"))
async def max_gas_price_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    message = "Please provide the gas price delta: how much extra SOL would you like to add the tx faster? Typically, a value between 0.001-0.005 is recommended."
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="3"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_gas_delta)



@user_settings_menu.message(StateFilter(UserSettingsState.set_gas_delta))
async def max_gas_price(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.max_gas_price = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode = "MarkDown")
        await state.clear()
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 0.001, 0.1 etc")
        await state.clear()





@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="min_liquidity"), StateFilter("*"))
async def min_liquidity_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    
    unit = "SOL"
    message = f"Please specify the minimum liquidity addition (in {unit}) required to initiate a snipe. For example, you might choose a value like 10. "
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="10"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_min_liq)



@user_settings_menu.message(StateFilter(UserSettingsState.set_min_liq))
async def min_liquidity(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.min_liquidity = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode = "MarkDown")
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
    await state.clear()


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="set_slippage_settings"), StateFilter("*"))
async def set_slippage_settings_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    message = f"Please set slippage for {setting.network} network in percentage. e.g.: 10, 20%"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="10"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_slippage)



@user_settings_menu.message(StateFilter(UserSettingsState.set_slippage))
async def set_slippage_settings(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag.replace('%','')))
        setting = await state.get_data()
        setting = setting['setting']
        setting.slippage = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode = "MarkDown")
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
    await state.clear()


@user_settings_menu.callback_query(UserSettingsAction.filter(F.column=="set_sell_slippage_settings"), StateFilter("*"))
async def set_sell_slippage_settings_cb(query: types.CallbackQuery, callback_data: CallbackData, state: FSMContext):
    setting = await get_user_settings(query.from_user.id,  db)
    if not setting:
        setting = await add_new_settings(query)
    message = f"Please set sell slippage for ethereum network in percentage. e.g.: 10, 20%"
    await query.message.reply(text=message, reply_markup=ForceReply(input_field_placeholder="10"))
    await state.set_data({"setting":setting})
    await state.set_state(UserSettingsState.set_slippage)



@user_settings_menu.message(StateFilter(UserSettingsState.set_slippage))
async def set_sell_slippage_settings(message: types.Message, state: FSMContext):
    messag = message.text
    try:
        amount = abs(float(messag))
        setting = await state.get_data()
        setting = setting['setting']
        setting.sell_slippage = amount
        new_settings = await set_user_setting(setting, db)
        text1 = get_settings_message(new_settings)
        # print(text1)
        await message.reply(text=text1, reply_markup=user_settings_keyboard(network=new_settings.network), parse_mode = "MarkDown")
    except Exception as e:
        print(e)
        await message.reply("Please provide a valid number e.g. 10.5, 50 etc")
    await state.clear()





