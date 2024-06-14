from utils.solana_trade_utils import solana_base, SolanaUtils

from utils.config import LAMPORTS_PER_SOL, TIP_ACCOUNTS, SOLANA_RPC
import random
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.signature import Signature
from utils.jito_script import send_bundle_txs_input
import json

from threading import Thread
import asyncio
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BUY_STEP = float(os.getenv("BUY_STEP"))
INIT_BUY = float(os.getenv("INIT_BUY"))
JITO_TIP = float(os.getenv("JITO_TIP"))
# def confirm_sol_tx(base, network, user, coin, amount, tx_hash_, out_qty, direction, eth_out=0, retries=5):
def confirm_sol_tx(hash_value, user, direction, web3, network, base, coin, amount, out_qty, event_loop, order_data=None, retries=20):
    print("8. Confirm transaction...")
    solana_client = Client(endpoint=SOLANA_RPC, commitment='confirmed')
    while retries:
        time.sleep(2)
        try:
            if type(hash_value)==str:
                hash_value = Signature.from_string(hash_value)
            status = solana_client.get_transaction(hash_value,"json")
            FeesUsed = (status.value.transaction.meta.fee) / 1000000000
            if status.value.transaction.meta.err == None:
                print("[create_account] Transaction Success",status.value)
                print(f"[create_account] Transaction Fees: {FeesUsed:.10f} SOL")
                future = asyncio.run_coroutine_threadsafe(ca_handler.transfer_fee(base=base, network='solana', user=user, coin=coin, amount=amount, tx_hash_=hash_value, out_qty=out_qty, direction=direction, order_data=order_data), event_loop) 
                print(future.result())
                return hash_value
        except Exception as e:
            print(f"Error while confirm Tx: {e}")
            retries -= 1
    return False


async def get_buy_tx_for_user(payer, mint, poolKeys, base, amount):
    
    
    balance = base.get_sol_balance(payer.pubkey())
    print(f"Balance: {balance} | Amount: {amount}")
    if balance>0:
        if balance > (amount):
            min_out_amount =  0
            tx_data= base.get_buy_tx(token_contract=mint, amount=int(amount*LAMPORTS_PER_SOL), payer=payer, minAmountOut=min_out_amount, poolKeys=poolKeys, priority_fee=0)
            return tx_data
    return None


async def buy_for_users_in_bundle(payers, mint, poolKeys, amount=None):
    print(f'Creating buy bundle for {len(payers)} users.')
    bundle_txs = []
    bundle_sigs = {}
    base_amount = INIT_BUY
    mint = str(mint)
    for payer in payers:
        base = SolanaUtils(payer=payer, token_address=mint)
        tx = await get_buy_tx_for_user(payer, mint, poolKeys, base, base_amount)
        if tx:
            bundle_sigs[str(tx.signature())] = [str(payer.pubkey()), base_amount]
            bundle_txs.append(tx)
        if len(bundle_txs)==4:
            sig = send_bundle_txs_input(solana_base.web3, payers, bundle_txs, int(JITO_TIP*LAMPORTS_PER_SOL), random.choice(TIP_ACCOUNTS))
            bundle_txs = []
        base_amount += BUY_STEP
    if bundle_txs:
        sig = send_bundle_txs_input(solana_base.web3, payers, bundle_txs, int(JITO_TIP*LAMPORTS_PER_SOL), random.choice(TIP_ACCOUNTS))
    return sig, bundle_sigs


async def get_all_buy_txs(payers, mint, poolKeys, amount=None):
    print(f'Creating buy bundle for {len(payers)} users.')
    all_txs = []
    all_signers = []
    bundle_sigs = {}
    base_amount = INIT_BUY
    mint = str(mint)
    for payer in payers:
        base = SolanaUtils(payer=payer, token_address=mint)
        tx_data = await get_buy_tx_for_user(payer, mint, poolKeys, base, base_amount)
        tx = tx_data['tx']
        if tx:
            bundle_sigs[str(tx_data['tx'].signature())] = [str(payer.pubkey()), base_amount]
            all_txs.append(tx)
            all_signers.append(tx_data)
        
        base_amount += BUY_STEP
    
    return all_txs, bundle_sigs, all_signers


async def prepare_bundle_and_send(payers, all_txs, bundle_sigs, amount=None, all_signers=[]):
    
    bundle_txs = []
    print(len(all_txs))
    print(len(all_signers))
    for i,tx in enumerate(all_txs):
        
        blockhash = solana_base.web3.get_latest_blockhash().value.blockhash
        tx = all_signers[i]['tx']
        signers = all_signers[i]['signers']
        tx.recent_blockhash = blockhash
        tx.sign(*signers)
        bundle_txs.append(tx)
        if len(all_txs)==4:
            sig = send_bundle_txs_input(solana_base.web3, payers, bundle_txs, int(JITO_TIP*LAMPORTS_PER_SOL), random.choice(TIP_ACCOUNTS))
            bundle_txs = []
        
    if bundle_txs:
        sig = send_bundle_txs_input(solana_base.web3, payers, bundle_txs, int(JITO_TIP*LAMPORTS_PER_SOL), random.choice(TIP_ACCOUNTS))
    return sig, bundle_sigs

async def spam_buys(payers, mint, poolKeys):
    starting_balance = solana_base.get_sol_balance(wallet=payers[0].pubkey())    
    mint = str(mint)
    
    all_txs, bundle_sigs, all_signers = await get_all_buy_txs(payers, mint, poolKeys)
    while True:
        
        current_balance = solana_base.get_sol_balance(wallet=payers[0].pubkey())
        if starting_balance==current_balance:
            sig, bundle_sigs = await prepare_bundle_and_send(payers, all_txs, bundle_sigs, all_signers=all_signers)
            time.sleep(0.5)
        else:
            return sig, bundle_sigs



async def get_sell_tx_for_user(payer, mint, poolKeys):
    
    base = SolanaUtils(payer=payer, token_address=mint)
    balance = base.get_token_balance(mint)
    if balance>0:
        min_out_amount =  0
        tx = base.get_sell_tx(token_contract=mint, amount=int(balance), payer=payer, minAmountOut=min_out_amount, poolKeys=poolKeys, priority_fee=0)
        return tx
    return None



async def sell_for_users_in_bundle(payers, mint, poolKeys):
    print(f'Creating sell bundle for {len(payers)} users.')
    bundle_txs = []
    bundle_sigs = {}
    mint = str(mint)
    for payer in payers:
        tx = await get_sell_tx_for_user(payer, mint, poolKeys)
        if tx:
            bundle_sigs[str(tx.signature())] = [str(payer.pubkey()), 0]
            bundle_txs.append(tx)
        if len(bundle_txs)==4:
            sig = send_bundle_txs_input(solana_base.web3, payers, bundle_txs, int(JITO_TIP*LAMPORTS_PER_SOL), random.choice(TIP_ACCOUNTS))
            bundle_txs = []
    if bundle_txs:
        sig = send_bundle_txs_input(solana_base.web3, payers, bundle_txs, int(JITO_TIP*LAMPORTS_PER_SOL), random.choice(TIP_ACCOUNTS))
    return sig, bundle_sigs



async def confirm_sig(sig, retries=12):
    print("8. Confirm transaction...")
    solana_client = Client(endpoint=SOLANA_RPC, commitment='confirmed')
    while retries:
        time.sleep(3)
        try:
            if type(hash_value)==str:
                hash_value = Signature.from_string(sig)
            status = solana_client.get_transaction(hash_value,"json")
            FeesUsed = (status.value.transaction.meta.fee) / 1000000000
            if status.value.transaction.meta.err == None:
                print("[create_account] Transaction Success",status.value)
                print(f"[create_account] Transaction Fees: {FeesUsed:.10f} SOL")
                # future = asyncio.run_coroutine_threadsafe(ca_handler.transfer_fee(base=base, network='solana', user=user, coin=coin, amount=amount, tx_hash_=hash_value, out_qty=out_qty, direction="buy", order_data=order_data), event_loop) 
                # print(future.result())
                return True
        except Exception as e:
            print(f"Error while confirm Tx: {e}")
            retries -= 1
    return False
 