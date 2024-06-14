# handlers/start.py
from aiogram import types
from aiogram.fsm.context import FSMContext


from bot.keyboards.paid_user_kb import start_menu_keyboard, default_menu_keyboard, settings_zone_keyboard, trade_zone_keyboard, faq_zone_keyboard
from bot.keyboards.menu_keyboard import wallet_manager_keyboard

from bot.db_client import db, get_db
from bot.kb_texts.all_messages import no_wallet
from database.user_functions import  get_user_by_chat_id, get_all_users


from aiogram.filters import Command, StateFilter
from bot.callback_factories.back import Back
from bot.callback_factories.start_action import StartAction
from bot.handlers.routers import start_menu
from bot.kb_texts.all_messages import home_message, settings_message, snipe_zone_message, faq_zone_message, start_message
from aiogram import F
from aiogram.types import FSInputFile

from aiogram.exceptions import TelegramBadRequest


@start_menu.callback_query(Back.filter(F.type=="main_menu"), StateFilter('*'))
async def start_func(query: types.CallbackQuery, state):
    await state.set_state(None)
    user_data = await get_user_by_chat_id(query.from_user.id, db)
    network = user_data.active_network
    has_wallet = True if [x for x in user_data.wallets if x.network.lower()==network.lower()] else False
    if not has_wallet:
        if query.message.text:
            await query.message.edit_text(text=no_wallet, reply_markup=wallet_manager_keyboard(user_data, False),parse_mode='MarkDown')
        else:
            await query.message.answer(text=no_wallet, reply_markup=wallet_manager_keyboard(user_data, False),parse_mode='MarkDown')
        return
    kb = default_menu_keyboard(user_data)
    text= home_message
    try:
        if query.message.text:
            out_message =  await query.message.edit_text(text=text, reply_markup=kb,parse_mode='MarkDown')
        else:
            # photo_path = ("bot/kb_texts/TG.jpg")
            # with open(photo_path, 'rb') as photo_file:
            #     photo = FSInputFile(photo_path)
            out_message = await query.message.reply(text=text, reply_markup=kb,parse_mode='MarkDown')
            # try:
            #     await query.message.bot.pin_chat_message(chat_id=query.from_user.id, message_id=out_message.message_id, disable_notification=True)
            # except Exception as e:
            #     print(f"Error while pinning: {e}")
            #     pass
        
    except TelegramBadRequest:
        await query.message.delete()
        await query.message.answer(text, reply_markup=kb,parse_mode='MarkDown', disable_web_page_preview=True)
    
    return

@start_menu.callback_query(StartAction.filter(F.type=="settings_zone"), StateFilter('*'))
async def settings_zone_cb(query: types.CallbackQuery, state):
    await state.set_state(None)
    user_data = await get_user_by_chat_id(query.from_user.id, db)
    
    kb = settings_zone_keyboard(user_data)
    
    text= settings_message

    try:
        if query.message.text:
            await query.message.edit_text(text=text, reply_markup=kb,parse_mode='MarkDown')
        else:
            await query.message.answer(text=text, reply_markup=kb,parse_mode='MarkDown')
    except TelegramBadRequest:
        await query.message.delete()
        await query.message.answer(text, reply_markup=kb,parse_mode='MarkDown', disable_web_page_preview=True)
    return

@start_menu.callback_query(StartAction.filter(F.type=="snipe_zone"), StateFilter('*'))
async def snipe_zone_cb(query: types.CallbackQuery, state):
    await state.set_state(None)
    user_data = await get_user_by_chat_id(query.from_user.id, db)

    kb = trade_zone_keyboard(user_data)
    
    text = snipe_zone_message.format(user_data.active_network.title(), user_data.active_network.title())

    try:
        if query.message.text:
            await query.message.edit_text(text=text, reply_markup=kb,parse_mode='MarkDown')
        else:
            await query.message.answer(text=text, reply_markup=kb,parse_mode='MarkDown')
    except TelegramBadRequest:
        await query.message.delete()
        await query.message.answer(text, reply_markup=kb,parse_mode='MarkDown', disable_web_page_preview=True)
    return


@start_menu.callback_query(StartAction.filter(F.type=="faq_zone"), StateFilter('*'))
async def faq_zone_cb(query: types.CallbackQuery, state):
    await state.set_state(None)
    kb = faq_zone_keyboard()

    text = faq_zone_message


    try:
        if query.message.text:
            await query.message.edit_text(text=text, reply_markup=kb,parse_mode='MarkDown')
        else:
            await query.message.answer(text=text, reply_markup=kb,parse_mode='MarkDown')
    except TelegramBadRequest:
        await query.message.delete()
        await query.message.answer(text, reply_markup=kb,parse_mode='MarkDown', disable_web_page_preview=True)
    return




@start_menu.message(Command(commands=["start"]), StateFilter("*"))
async def start_command(message: types.Message, state:FSMContext):
    await state.clear()
    await state.set_state(None)
    user_data = await get_user_by_chat_id(message.from_user.id, db)
    text= home_message
    photo_path = ("bot/kb_texts/TG.png")
    with open(photo_path, 'rb') as photo_file:
        photo = FSInputFile(photo_path)
    out_message = await message.answer_photo(photo=photo, caption=text, parse_mode="MarkDown", reply_markup=start_menu_keyboard())
    # await message.reply(text=text, parse_mode='MarkDown', reply_markup=start_menu_keyboard())
    
    
@start_menu.message(Command(commands=["notify_1357"]), StateFilter("*"))
async def start_command1(message: types.Message, state:FSMContext):
    await state.clear()
    await state.set_state("notifying_all")
    # user_data = await get_user_by_chat_id(message.from_user.id, db)
    
    await message.reply(text="Please reply with the message that you want to send to all users.", parse_mode='MarkDown', reply_markup=types.ForceReply())

@start_menu.message(StateFilter("notifying_all"))
async def start_command2(message: types.Message, state: FSMContext):
    text = message.text
    users = await get_all_users(get_db())
    
    for user_id in users:
        await message.bot.send_message(chat_id=user_id, text=text)


    