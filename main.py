import asyncio
import websockets
import json
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.signature import Signature
from utils.solana_metadata.helper import get_metadata
from utils.solana_trade_utils import SolanaUtils, solana_base
import asyncio
from datetime import datetime  # Import datetime for timestamps
import os
import random
import sys

import regex as re
import telebot
from telethon import TelegramClient
from twikit.twikit_async import Client
from utils.get_pool_keys import get_pool_data
from utils.sol_swaps import spam_buys, sell_for_users_in_bundle

from utils.raydium.buy_swap import buy as buy_raydium
from spl.token.client import Client

import time
from datetime import datetime

from spl.token.client import Token
from utils.config import SOLANA_RPC, TOKEN_PROGRAM_OWNER_ID, SELL_TIME_SECONDS, TARGET_TOKEN, MINT_AUTHORITY
from pool_keys import Liquidity
import re
import json
import os
from dotenv import load_dotenv
from cryptocompare import get_price

# Load environment variables from .env file
load_dotenv()



TOKEN_PROGRAM_OWNER_ID = TOKEN_PROGRAM_OWNER_ID

SOLANA_RPC_WEBSOCKET = os.getenv("SOLANA_RPC_WEBSOCKET")
PRIVATE_KEYS = json.loads(os.getenv("PRIVATE_KEYS"))
BUY_STEP = os.getenv("BUY_STEP")
payers = [Keypair.from_base58_string(x) for x in PRIVATE_KEYS]
[print(x.pubkey()) for x in payers]

seen_signatures = set()
solana_client = Client(SOLANA_RPC, commitment='processed')
solana_base.web3 = solana_client
solana_base.payer = payers[0]
spl_client = Client(endpoint=SOLANA_RPC)

OPENBOOK = Pubkey.from_string('srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX')
RAYDIUM_PROGRAM_ID = Pubkey.from_string('675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8')
TOKEN_PROGRAM = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
SOL = Pubkey.from_string('So11111111111111111111111111111111111111112')

async def confirm_sol_tx_simple(hash_value, solana_client, retries=20):
    print("8. Confirm transaction...")
    while retries:
        await asyncio.sleep(2)
        try:
            status = solana_client.get_transaction(hash_value, encoding="json", commitment='confirmed')
            FeesUsed = (status.value.transaction.meta.fee) / 1000000000
            if status.value.transaction.meta.err is None:
                print("[create_account] Transaction Success", status.value)
                print(f"[create_account] Transaction Fees: {FeesUsed:.10f} SOL")
                return True
        except Exception as e:
            print(f"Awaiting Transaction Confirmation... {e}")
            retries -= 1
    return False

async def confirm_sol_tx(hash_value, base, retries=10):
    print("8. Confirm transaction...")
    solana_client = base.web3
    while retries:
        await asyncio.sleep(2)
        try:
            status = solana_client.get_transaction(hash_value, "json")
            FeesUsed = (status.value.transaction.meta.fee) / 1000000000
            if status.value.transaction.meta.err is None:
                return hash_value
        except Exception as e:
            print(f"Awaiting Transaction Confirmation... {e}")
            retries -= 1
    return False

def get_sol_client(commitment):
    return Client(SOLANA_RPC, commitment=commitment)

async def getTokens(str_signature, token_address):
    if type(token_address) == str:
        Token0 = Pubkey.from_string(token_address)
    tx_sig = Signature.from_string(str_signature)
    transaction = solana_client.get_transaction(tx_sig, encoding="jsonParsed", max_supported_transaction_version=0, commitment='confirmed').value
    if transaction:
        instruction_list = transaction.transaction.transaction.message.instructions
        for instructions in instruction_list:
            if instructions.program_id == OPENBOOK:
                if any(token_address in str(address) for address in instructions.accounts):
                    print(f"True, https://solscan.io/tx/{str_signature}")
                    market_id = instructions.accounts[0]
                    token_program_id = instructions.accounts[5]
                    mint_address = instructions.accounts[7]
                    if token_address == str(mint_address):
                        await trigger_buy(mint_address, market_id, Token0)
    return False

async def trigger_buy(mint_address, market_id, Token0):
    spl = Token(conn=solana_client, pubkey=mint_address, program_id=TOKEN_PROGRAM, payer=Keypair())
    mint_info = spl.get_mint_info()
    base_decimals = mint_info.decimals
    quote_decimals = 9
    # if MINT_AUTHORITY:
    #     if not mint_info.mint_authority:
    #         print('Mint authority not revoked!')
    #         return
    pool_keys = Liquidity.getAssociatedPoolKeys(4, 3, marketId=market_id, baseMint=mint_address, quoteMint=SOL, baseDecimals=base_decimals, quoteDecimals=quote_decimals, programId=RAYDIUM_PROGRAM_ID, marketProgramId=OPENBOOK)
    print(pool_keys)
    tx_hash, all_sigs = await spam_buys(payers=payers, mint=Token0, poolKeys=pool_keys)

    print(f"Bought successfully! | Datetime: {str(datetime.now())}")
    os._exit();
    await asyncio.sleep(SELL_TIME_SECONDS)
    rty = 0
    while rty > 0:
        tx_hash, all_sigs = await sell_for_users_in_bundle(payers, Token0, pool_keys)
        print(f'Sell Tx Hash: {tx_hash}')
        if type(tx_hash) != str and tx_hash is not None:
            response = await confirm_sol_tx_simple(tx_hash, get_sol_client('confirmed'))
            if response:
                return
            else:
                rty -= 1
                continue
    else:
        print(f"Unable to sell in retries. Quitting now.")
    return None

from utils.check_market_id import check_for_market_id

async def run(token_address):
    print(f'\nScanning token: {token_address}')
    print(f'processing buy')
    market_id = check_for_market_id(token_address)
    await trigger_buy(mint_address=Pubkey.from_string(token_address), market_id=Pubkey.from_string(market_id), Token0=Pubkey.from_string(token_address))
    return

async def main():
    while True:
        try:
            token_address = sys.argv[1]
            await run(token_address=token_address)
        except KeyboardInterrupt:
            break

asyncio.run(main())
