from aiogram import Router, F


wallet_menu = Router(name='wallet_menu')

wallet_menu.message.filter(F.chat.type == 'private')
wallet_menu.callback_query.filter(F.message.chat.type == 'private')

start_menu = Router(name='start_menu')
start_menu.message.filter(F.chat.type == 'private')
start_menu.callback_query.filter(F.message.chat.type == 'private')


payment_menu = Router(name='payment_menu')
payment_menu.message.filter(F.chat.type == 'private')
payment_menu.callback_query.filter(F.message.chat.type == 'private')


ca_menu = Router(name='ca_menu')
ca_menu.message.filter(F.chat.type == 'private')
ca_menu.callback_query.filter(F.message.chat.type == 'private')

group_handler = Router(name="group_handler")

user_settings_menu = Router(name='user_settings')
user_settings_menu.message.filter(F.chat.type == 'private')
user_settings_menu.callback_query.filter(F.message.chat.type == 'private')
