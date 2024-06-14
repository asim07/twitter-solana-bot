from solders.pubkey import Pubkey
from solana.rpc.api import Client
from utils.layouts import MARKET_LAYOUT , AMM_INFO_LAYOUT_V4, MINT_LAYOUT
from utils.config import SOLANA_RPC, RAYDIUM_PUBLIC_KEY
import time




def get_pool_data(client, pool_address):
    poolPubKey = Pubkey.from_string(pool_address)
    while True:
        
        poolData = client.get_account_info(poolPubKey)
        if poolData.value:
            break
        print(f"Retrying to get pool keys: {pool_address}")
        time.sleep(1)

    info = poolData.value.data
    lp_data = AMM_INFO_LAYOUT_V4.parse(info)
    
    serumData = client.get_account_info(Pubkey.from_bytes(lp_data.market_id))
    data = serumData.value.data
    marketLpData = MARKET_LAYOUT.parse(data)

    vault_signer = Pubkey.create_program_address(
            [bytes(Pubkey.from_bytes(lp_data.market_id)), marketLpData.vault_signer_nonce.to_bytes(8, byteorder="little")],
            Pubkey.from_bytes(lp_data.serum_program_id)
        )
    
    lpMint = Pubkey.from_bytes(lp_data.lp_mint)
    lpMintAccount = client.get_account_info(lpMint)
    if lpMintAccount is None: raise ValueError('get lp mint info error')
    lpMintInfo = MINT_LAYOUT.parse(lpMintAccount.value.data)

    outpool_data = {
    'amm_id': str(poolPubKey),
    'base_mint': str(Pubkey.from_bytes(marketLpData.base_mint)),
    'quote_mint': str(Pubkey.from_bytes(marketLpData.quote_mint )),
    'lp_mint': str(Pubkey.from_bytes(lp_data.lp_mint)),
    'base_decimal': str(int(lp_data.base_decimal)),
    'quote_decimal': int(lp_data.quote_decimal),
    'lp_decimals': lpMintInfo.decimals,
    'version': 4,
    'market_version': 3,
    'program_id': RAYDIUM_PUBLIC_KEY,
    'authority': "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
    'open_orders': str(Pubkey.from_bytes(lp_data.open_orders)),
    'target_orders': str(Pubkey.from_bytes(lp_data.target_orders)),
    'base_vault': str(Pubkey.from_bytes(lp_data.base_vault)),
    'quote_vault': str(Pubkey.from_bytes(lp_data.quote_vault)),
    'lp_vault': str(Pubkey.from_bytes(lp_data.lp_vault)),
    'withdraw_queue': str(Pubkey.from_bytes(lp_data.withdraw_queue)),
    'market_program_id': str(Pubkey.from_bytes(lp_data.serum_program_id)),
    'market_id': str(Pubkey.from_bytes(lp_data.market_id)),
    'market_authority': str(vault_signer),
    'market_base_vault': str(Pubkey.from_bytes(marketLpData.base_vault)),
    'market_quote_vault': str(Pubkey.from_bytes(marketLpData.quote_vault)),
    'bids': str(Pubkey.from_bytes(marketLpData.bids)),
    'asks': str(Pubkey.from_bytes(marketLpData.asks)),
    'event_queue': str(Pubkey.from_bytes(marketLpData.event_queue)),
    'lookup_table_account': str(Pubkey.default())
    }

    return outpool_data