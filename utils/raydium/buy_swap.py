from spl.token.instructions import close_account, CloseAccountParams
from spl.token.client import Token
from spl.token.core import _TokenCore
import json
from solana.rpc import types
from solana.rpc.commitment import Commitment
from solana.rpc.api import RPCException
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from utils.config import SWAP_COMPUTE_LIMIT, SWAP_COMPUTE_PRICE, TIP_ACCOUNTS
from solana.transaction import Transaction
from utils.raydium.create_close_account import get_token_account,get_transfer_instruction, get_token_account, make_swap_instruction, compute_units_limit_inx, compute_units_price_inx

from utils.jito_script import send_bundle

import random


import time

LAMPORTS_PER_SOL = 1000000000


def buy(solana_client, TOKEN_TO_SWAP_BUY, payer, amount, minAmountOut, poolKeys, compute_price=None, compute_limit=None, retries=3, priority_fee=None, return_tx=False):
    token_symbol, SOl_Symbol = "NM"
    if priority_fee:
        priority_fee= int(float(priority_fee) * LAMPORTS_PER_SOL)
    else:
        priority_fee = 100000
    # mint = Pubkey.from_string(TOKEN_TO_SWAP_BUY)
    mint = TOKEN_TO_SWAP_BUY
    
    # pool_keys = fetch_pool_keys(str(mint))
    pool_keys = poolKeys

    
    """
    Calculate amount
    """
    mint = Pubkey.from_string(mint) if type(mint)==str else mint
    amount_in = int(amount)
    if amount_in==0:
        amount_in = int(amount*LAMPORTS_PER_SOL)
    # return

    txnBool = True
    while txnBool:
        instructions = []
        """Get swap token program id"""
        print("1. Get TOKEN_PROGRAM_ID...")
        accountProgramId = solana_client.get_account_info_json_parsed(mint)
        
        pID = json.loads(accountProgramId.to_json())
        
        TOKEN_PROGRAM_ID = pID['result']['value']['owner']
        TOKEN_PROGRAM_ID = Pubkey.from_string(TOKEN_PROGRAM_ID)

        """
        Set Mint Token accounts addresses
        """
        print("2. Get Mint Token accounts addresses...")
        swap_associated_token_address,swap_token_account_Instructions  = get_token_account(solana_client, payer.pubkey(), mint)


        """
        Create Wrap Sol Instructions
        """
        print("3. Create Wrap Sol Instructions...")
        balance_needed = Token.get_min_balance_rent_for_exempt_for_account(solana_client)
        print(f"balance_needed {balance_needed}")
        WSOL_token_account, swap_tx, payer, Wsol_account_keyPair, opts, = _TokenCore._create_wrapped_native_account_args(program_id=TOKEN_PROGRAM_ID, owner=payer.pubkey(), payer=payer, amount=amount_in,
                                                            skip_confirmation=False, balance_needed=balance_needed, commitment=Commitment("processed"))


        instructions.extend(list(swap_tx.instructions))

        print("4. Create Swap Instructions...")
        instructions_swap = make_swap_instruction(  amount_in, 
                                                    WSOL_token_account,
                                                    swap_associated_token_address,
                                                    pool_keys, 
                                                    mint, 
                                                    solana_client,
                                                    payer,
                                                    minAmountOut
                                                )
        try:
            cp_ins = compute_units_price_inx(SWAP_COMPUTE_PRICE)
            swap_tx.add(cp_ins)
            instructions.append(cp_ins)
            # if compute_limit:
            cl_ins = compute_units_limit_inx(SWAP_COMPUTE_LIMIT)
            print(f"Compute Fee in Sol: {SWAP_COMPUTE_LIMIT*SWAP_COMPUTE_PRICE*(10**(-9))*(10**(-6))} SOL")
            swap_tx.add(cl_ins)
            instructions.append(cl_ins)
        except Exception as e:
            print(f"Compute fee ins: {e}")


        
        print("5. Create Close Account Instructions...")
        params = CloseAccountParams(account=WSOL_token_account, dest=payer.pubkey(), owner=payer.pubkey(), program_id=TOKEN_PROGRAM_ID)
        closeAcc =(close_account(params))

        print("6. Add instructions to transaction...")
        if swap_token_account_Instructions != None:
            swap_tx.add(swap_token_account_Instructions)
            instructions.append(swap_token_account_Instructions)
        swap_tx.add(instructions_swap)
        instructions.append(instructions_swap)
        swap_tx.add(closeAcc)
        instructions.append(closeAcc)

        try:
            while retries:
                try:
                    print("7. Execute Transaction...")
                    print(f'swap_tx {swap_tx}, payer {payer}, WSOL Account KPair {Wsol_account_keyPair}')
                    start_time = time.time()
                    # txn = solana_client.send_transaction(swap_tx, payer, Wsol_account_keyPair)
                    # txid_string_sig = txn.value
                    # return txid_string_sig
                    if not return_tx:
                        resp = send_bundle(solana_client, [payer, Wsol_account_keyPair], instructions, priority_fee, random.choice(TIP_ACCOUNTS))
                        return resp
                    else:
                        blockhash = solana_client.get_latest_blockhash().value.blockhash
                        swap_tx_v2 = Transaction(recent_blockhash=blockhash,instructions=instructions,fee_payer=payer.pubkey())
                        # swap_tx_v2.sign(payer, Wsol_account_keyPair)
                        # swap_tx.sign(payer, Wsol_account_keyPair)
                        return {'tx': swap_tx_v2, "signers":[payer, Wsol_account_keyPair]}
                      
                    
                except Exception as e:
                    print("Retry Sending TX")
                    print(f"ERROR : {e}")
                    retries -= 1
                    txnBool = False
                    

        except RPCException as e:
            if "Error processing Instruction 4" in e.args[0].message:
                print(f'Swap not possible: [{e.args[0].message}]')
                print(f'Swap not possible: [{e}]')
                return "failed"
            print(f"Error: [{e.args[0].message}]...\nRetrying...")
            if "insufficient funds" in str(e.args[0].data.logs):
                print("infufficient funds!")
                return "infufficient funds!"
            if 'exceeds desired slippage limit' in str(e.args[0].data.logs):
                print('Insufficient Slippage.')
                return 'Insufficient Slippage.'
            else:
                # print(f"e|Buy ERROR {token_symbol}",f"[Raydium]: {e.args[0].data.logs}")
                print(f"e|Buy ERROR coin is rugged can't be bought ")
                return "failed"

        except Exception as e:
            print(f"e|BUY Exception ERROR {token_symbol}",f"[Raydium]: {e}")
            
            txnBool = False
            return "failed"
