import json, time
from utils.config import  SOLANA_RPC, LAMPORTS_PER_SOL, TOKEN_PROGRAM_OWNER_ID, TRANSFER_COMPUTE_PRICE, TRANSFER_COMPUTE_LIMIT, TIP_ACCOUNTS
from utils.layouts import *
import logging
from solana.rpc import types
from spl.token.client import Token
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solders.keypair import Keypair
from utils.raydium.buy_swap import buy as buyRaydium
from utils.raydium.sell_swap import sell as sellRaydium
from utils.raydium.create_close_account import compute_units_limit_inx, compute_units_price_inx
import requests

from utils.jito_script import send_bundle

import random



class SolanaUtils:
    
    def __init__(self, web3: Client = None, payer=None, token_address: str = "0xdAC17F958D2ee523a2206206994597C13D831ec7", private_key: str = None):
        self.logger = self.get_logger()
        if not payer:
            try:
                self.payer = Keypair.from_base58_string(private_key) if private_key else Keypair()
            except:
                print('here')
        else:
            self.payer = payer
        self.name = "solana_utils"
        self.web3 = web3
        self.token_address = token_address
        self.LAMPORTS_PER_SOL = LAMPORTS_PER_SOL
        
        if not self.web3:
            self.web3 = Client(SOLANA_RPC, commitment='processed')
        self.spl = Token(conn=self.web3, pubkey=Pubkey.from_string(self.token_address), program_id=Pubkey.from_string(TOKEN_PROGRAM_OWNER_ID), payer=self.payer)
        
        self.wallet = self.payer.pubkey()
        

    @classmethod
    def get_cu_price(self, microlamports):
        return set_compute_unit_price(int(microlamports))
    @classmethod
    def get_cu_limit(self, units):
        return set_compute_unit_limit(int(units))

    def get_spl_class(self, token_address: str, payer: Keypair=None):
        payer = Keypair()
        return Token(conn=self.web3, pubkey=Pubkey.from_string(token_address), program_id=Pubkey.from_string(TOKEN_PROGRAM_OWNER_ID), payer=self.payer if not payer else payer)


    def get_logger(self):
        logger = logging.getLogger("Solana Utils")
        logging.basicConfig(
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                )
        return logger

    def get_mint_info(self, tokenAddress):
        spl = self.get_spl_class(token_address=tokenAddress)
        return spl.get_mint_info()

    def transfer_sol(self, to: str, amount: int, priority_fee: float=0):
        priority_fee = int(float(priority_fee) * LAMPORTS_PER_SOL)
        print(f'Sending from the account: {self.payer.pubkey()}')
        receiver = Pubkey.from_string(to)
        amount_in_lamports = (self.LAMPORTS_PER_SOL * amount) - 5000
        transfer_ix = transfer(TransferParams(from_pubkey=self.payer.pubkey(), to_pubkey=receiver, lamports=int(amount_in_lamports)))     
        ixs = [transfer_ix]
        signers = [self.payer]
        # txn.sign(*signers)
        tx_sig = send_bundle(self.web3, signers, ixs, priority_fee, random.choice(TIP_ACCOUNTS))
        # tx_sig = self.web3.send_transaction(txn, *signers)
        print("Transfer Fee TX : ",tx_sig)

        return tx_sig

    def transfer_spl_token(self, token_contract: str, to: str, amount: int, payer: Keypair = None):
        spl_client = self.get_spl_class(token_address=token_contract, payer=payer)
        # recent_blockhash = self.web3.get_latest_blockhash().value
        # blockHash = recent_blockhash.blockhash
        source_token_account = (
            spl_client.get_accounts_by_owner(
                owner=payer.pubkey(), commitment=None, encoding="base64"
            )
            .value[0]
            .pubkey
        )
        dest = Pubkey.from_string(to)
        while True:
            try:
                dest_token_account = (
                    spl_client.get_accounts_by_owner(owner=dest, commitment=None, encoding="base64")
                    .value[0]
                    .pubkey
                )
                break
            except IndexError:
                try:
                    dest_token_account = spl_client.create_associated_token_account(
                        owner=dest, skip_confirmation=False, recent_blockhash=None
                    )
                    break
                except:
                    time.sleep(3)
                    continue

        recent_blockhash = self.web3.get_latest_blockhash().value
        blockHash = recent_blockhash.blockhash
        lastValidBlockHeight = json.loads(recent_blockhash.to_json())['lastValidBlockHeight']
        block_height = self.web3.get_block_height().value

        while int(block_height) < int(lastValidBlockHeight):
            try:
                print('.')
                amount = amount
                transaction = spl_client.transfer(
                    source=source_token_account,
                    dest=dest_token_account,
                    owner=payer,
                    amount=int(float(amount) * self.LAMPORTS_PER_SOL),
                    recent_blockhash=blockHash,
                    opts=types.TxOpts(skip_preflight=True, skip_confirmation=False, max_retries=3)
                )
                txn_response = transaction
                print(txn_response)
                return txn_response.value
            except:
                time.sleep(1)
                block_height = self.web3.get_block_height().value
                print('Sleeping due to block height')            

    def buy_raydium(self, token_contract: str, amount: int, payer: Keypair = None, minAmountOut=None, poolKeys={}, compute_price=None, compute_limit=None, priority_fee=None):
        tx_sig = buyRaydium(self.web3, token_contract, payer=payer, amount=amount, minAmountOut=minAmountOut, poolKeys=poolKeys,compute_price=compute_price, compute_limit=compute_limit,priority_fee=priority_fee, return_tx=False)
        print(f"Transaction Response : {tx_sig}")
        return tx_sig
    

    def get_buy_tx(self, token_contract: str, amount: int, payer: Keypair = None, minAmountOut=None, poolKeys={}, compute_price=None, compute_limit=None, priority_fee=None):
        tx_data = buyRaydium(self.web3, token_contract, payer=payer, amount=amount, minAmountOut=minAmountOut, poolKeys=poolKeys,compute_price=compute_price, compute_limit=compute_limit,priority_fee=priority_fee, return_tx=True )
        return tx_data
    
    
    def get_sell_tx(self, token_contract: str, amount: int, payer: Keypair = None, minAmountOut=None, poolKeys={}, compute_price=None, compute_limit=None, priority_fee=None):
        tx = sellRaydium(self.web3, token_contract, payer=payer, amount=amount, minAmountOut=minAmountOut, poolKeys=poolKeys,compute_price=compute_price, compute_limit=compute_limit,priority_fee=priority_fee, return_tx=True)
        return tx

    def sell_raydium(self, token_contract: str, amount: int, payer: Keypair = None, minAmountOut=None, poolKeys={}, compute_price=None, compute_limit=None, priority_fee=None):
        tx_sig = sellRaydium(self.web3, token_contract, payer=payer, amount=amount, minAmountOut=minAmountOut, poolKeys=poolKeys,compute_price=compute_price, compute_limit=compute_limit,priority_fee=priority_fee)
        print(f"Transaction Response : {tx_sig}")
        return tx_sig
    
    def approve(self, token_address, amount):
        pass
    
        


    def get_pair_address(self, token_a: str, token_b: str):
        pass

    def get_reserves(self, pair_address: str, pool_keys: dict=None):
        base_vault, quote_vault, base_mint = self.get_base_quote_vault(pair_address=pair_address, pool_keys=pool_keys)
        base_qty = self.spl.get_balance(base_vault).value.ui_amount
        quote_qty = self.spl.get_balance(quote_vault).value.ui_amount
        if "So11" in str(base_mint):
            return quote_qty, base_qty
        else:
            return base_qty, quote_qty


    def get_price_sol_in(self, pair_address: str, sol_in: float, pool_keys=None):
        price, base_mint = self.get_price(pair_address=pair_address, pool_keys=pool_keys)
        price = 1/price
        # price = ((base_qty)/(quote_qty)) * (sol_in)
        if "So11" in str(base_mint):
            return (sol_in) / price , price
        else:
            return (sol_in) * price , price
        
    
    def get_price_sol_out(self, pair_address: str, token_in: float, pool_keys=None):
        price, base_mint = self.get_price(pair_address=pair_address, pool_keys=pool_keys)
        if "So11" in str(base_mint):
            return float(token_in) / price 
        else:
            return float(token_in) * price 


    def get_price(self, pair_address: str, pool_keys: dict=None):
        base_vault, quote_vault, base_mint = self.get_base_quote_vault(pair_address=pair_address, pool_keys=pool_keys)
        base_qty = self.spl.get_balance(base_vault).value.ui_amount
        quote_qty = self.spl.get_balance(quote_vault).value.ui_amount
        price = ((quote_qty)/(base_qty))
        return price, base_mint

    def get_base_quote_vault(self, pair_address:str, pool_keys: dict=None):
        if not pool_keys:
            pool_data = self.web3.get_account_info(Pubkey.from_string(pair_address))
            info = (pool_data.value.data)
            contained_info = AMM_INFO_LAYOUT_V4.parse(info)
            base_vault = Pubkey.from_bytes(contained_info.base_vault)
            quote_vault = Pubkey.from_bytes(contained_info.quote_vault)
            base_mint = Pubkey.from_bytes(contained_info.base_mint)
        else:
            base_vault = Pubkey.from_string(pool_keys['base_vault'])
            quote_vault = Pubkey.from_string(pool_keys['quote_vault'])
            base_mint = Pubkey.from_string(pool_keys['base_mint'])
        
        return base_vault, quote_vault, base_mint


    def get_sol_balance(self, wallet: Pubkey=None):
        if not wallet:
            wallet = self.wallet
        return self.web3.get_balance(wallet).value/self.LAMPORTS_PER_SOL


    def get_token_balance(self, token_address: str):
        try:
            spl = self.get_spl_class(token_address=token_address)
            token_account = (spl.get_accounts_by_owner(self.payer.pubkey()))
            token_account = token_account.value[0].pubkey
            resp = spl.get_balance(token_account)
            return resp.value.ui_amount
        except Exception as e:
            print(f"Error while getting token balance: {e}")
            return 0    
        
    def get_token_balance_w_wallet(self, token_address: str, wallet: str):
        try:
            spl = self.get_spl_class(token_address=token_address)
            wallet = Pubkey.from_string(wallet)
            token_account = spl.get_accounts_by_owner(wallet)
            try:
                token_account = token_account.value[0].pubkey
            except IndexError:
                return 0
            resp = spl.get_balance(token_account)
            return resp.value.ui_amount
        except Exception as e:
            print(f"Error while getting token balance: {e}")
            return 0


    def get_dexscreener_price(self, pair_address: str):
        response = requests.get(f'https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}')
        response.raise_for_status()
        data = response.json()
        pair = None
        try:
            if data.get('pairs'):
                for pair1 in data.get('pairs', []):
                    # if pair1.get('quoteToken', "").get('symbol') in ["WMATIC"]:
                    if pair1.get('quoteToken', "").get('symbol') in ["SOL"]:
                        pair = pair1
                        break
                
                if pair:
                    return float(pair.get('priceNative'))
                else:
                    return None
            else:
                return None
        except Exception as e:
            print(e)
            return None
    

    def get_dexscreener_pair_detail(self, pair_address: str):
        response = requests.get(f'https://api.dexscreener.com/latest/dex/pairs/solana/{pair_address}')
        response.raise_for_status()
        data = response.json()
        pair_data = {}
        try:
            if data.get('pairs'):
                for pair1 in data.get('pairs', []):
                    # if pair1.get('quoteToken', "").get('symbol') in ["WMATIC"]:
                    if pair1.get('quoteToken', "").get('symbol') in ["SOL"]:
                        pair_data = pair1
                
                if pair_data:
                    return pair_data
                else:
                    return None
        except Exception as e:
            print(e)
            return None
solana_base = SolanaUtils( token_address=TOKEN_PROGRAM_OWNER_ID)



