from spl.token.instructions import close_account, CloseAccountParams

from solana.rpc.types import TokenAccountOpts
from solana.rpc.api import RPCException
from solana.transaction import Transaction

from solders.pubkey import Pubkey

from utils.raydium.create_close_account import  get_transfer_instruction, sell_get_token_account,get_token_account, make_swap_instruction, compute_units_price_inx, compute_units_limit_inx


from utils.config import SWAP_COMPUTE_LIMIT, SWAP_COMPUTE_PRICE, TIP_ACCOUNTS
from utils.jito_script import send_bundle

import random


LAMPORTS_PER_SOL = 1000000000

        # ctx ,     TOKEN_TO_SWAP_SELL,  keypair
def sell(solana_client, TOKEN_TO_SWAP_SELL, payer, amount, minAmountOut, poolKeys, compute_price=None, compute_limit=None, priority_fee=None, return_tx=False):
    
    token_symbol, SOl_Symbol = "NB"

    if priority_fee:
        priority_fee= int(float(priority_fee) * LAMPORTS_PER_SOL)
    else:
        priority_fee = 100000
    mint = Pubkey.from_string(TOKEN_TO_SWAP_SELL)
    sol = Pubkey.from_string("So11111111111111111111111111111111111111112")

    """Get swap token program id"""
    print("1. Get TOKEN_PROGRAM_ID...")
    TOKEN_PROGRAM_ID = solana_client.get_account_info_json_parsed(mint).value.owner

    """Get Pool Keys"""
    print("2. Get Pool Keys...")
    
    pool_keys = poolKeys
    
    
    txnBool = True
    while txnBool:
        instructions = []
        """Get Token Balance from wallet"""
        print("3. Get oken Balance from wallet...")
        if "So11" not in pool_keys['base_mint']:
            amount_in = int(amount * 10**int(pool_keys['base_decimal']))
            minAmountOut = int(minAmountOut * 10**int(pool_keys['quote_decimal']))
        else:
            amount_in = int(amount * 10**int(pool_keys['quote_decimal']))
            minAmountOut = int(minAmountOut * 10**int(pool_keys['base_decimal']))
        
        """Get token accounts"""
        print("4. Get token accounts for swap...")
        swap_token_account = sell_get_token_account(solana_client, payer.pubkey(), mint)
        WSOL_token_account, WSOL_token_account_Instructions = get_token_account(solana_client,payer.pubkey(), sol)
        
        if swap_token_account == None:
            print("swap_token_account not found...")
            return "failed"

        else:
            """Make swap instructions"""
            print("5. Create Swap Instructions...")
            instructions_swap = make_swap_instruction(  amount_in, 
                                                        swap_token_account,
                                                        WSOL_token_account,
                                                        pool_keys, 
                                                        mint, 
                                                        solana_client,
                                                        payer,
                                                        minAmountOut
                                                    )

            """Close wsol account"""
            print("6.  Create Instructions to Close WSOL account...")
            params = CloseAccountParams(account=WSOL_token_account, dest=payer.pubkey(), owner=payer.pubkey(), program_id=TOKEN_PROGRAM_ID)
            closeAcc =(close_account(params))


            
            
            """Create transaction and add instructions"""
            print("7. Create transaction and add instructions to Close WSOL account...")
            swap_tx = Transaction()
            
            signers = [payer]
            if WSOL_token_account_Instructions != None:
                swap_tx.add(WSOL_token_account_Instructions)
                instructions.append(WSOL_token_account_Instructions)
            cp_ins = compute_units_price_inx(SWAP_COMPUTE_PRICE)
            swap_tx.add(cp_ins)
            instructions.append(cp_ins)
            cl_ins = compute_units_limit_inx(SWAP_COMPUTE_LIMIT)
            swap_tx.add(cl_ins)
            swap_tx.add(instructions_swap)
            instructions.append(cl_ins)
            instructions.append(instructions_swap)
            # fee_ins = get_transfer_instruction(from_=str(payer.pubkey()), to= SOL_FEE_WALLET, amount=(SOL_FEE*2))
            # swap_tx.add(fee_ins)
            # instructions.append(fee_ins)
            swap_tx.add(closeAcc)
            instructions.append(closeAcc)

            """Send transaction"""
            try:
                print("8. Execute Transaction...")
                
                # txn = solana_client.send_transaction(swap_tx, *signers)
                # resp = send_bundle(solana_client, signers, instructions, priority_fee, random.choice(TIP_ACCOUNTS))
                if not return_tx:
                    resp = send_bundle(solana_client, signers, instructions, priority_fee, random.choice(TIP_ACCOUNTS))
                    return resp
                else:
                    blockhash = solana_client.get_latest_blockhash().value.blockhash
                    swap_tx_v2 = Transaction(recent_blockhash=blockhash,instructions=instructions,fee_payer=payer.pubkey())
                    swap_tx_v2.sign(payer)
                    return swap_tx_v2
                """Confirm it has been sent"""
                # txid_string_sig = txn.value
                return resp
            
            except RPCException as e:
                print(f"Error: [{e.args[0].message}]...\nRetrying...")
                if "insufficient funds" in str(e.args[0].data.logs):
                    print("infufficient funds!")
                    return "infufficient funds!"
                if 'exceeds desired slippage limit' in str(e.args[0].data.logs):
                    print('Insufficient Slippage.')
                    return 'Insufficient Slippage.'
                else:
                    print(f"e|SELL ERROR {token_symbol}",f"[Raydium]: {e.args[0].data.logs}")
                    return "failed"

            # except Exception as e:
            #     print(f"Error: [{e}]...\nEnd...")
            #     print(f"e|SELL Exception ERROR {token_symbol}",f"[Raydium]: {e.args[0].message}")
            #     txnBool = False
            #     return "failed"
