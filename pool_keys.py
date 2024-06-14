from typing import Any, Tuple
import logging
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from utils.config import SOLANA_RPC
from utils.layouts import AMM_INFO_LAYOUT_V4 as LIQUIDITY_VERSION_TO_STATE_LAYOUT, MARKET_LAYOUT
# Assume the necessary imports and constants are defined elsewhere, such as:
# from some_library import Connection, LiquidityPoolKeys, LiquidityPoolInfo, PublicKey, findProgramAddress, Market
OPENBOOK = 'srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX'

logger = logging.getLogger(__name__)

client = Client(SOLANA_RPC, commitment='processed')

def findProgramAddress(seeds, program_id):
    public_key, nonce = Pubkey.find_program_address(seeds, program_id)
    return {'public_key': public_key, 'nonce': nonce}

class Liquidity:
    # Assuming the Base class is defined elsewhere

    @staticmethod
    def getStateLayout(version: int) -> Any:
        STATE_LAYOUT = LIQUIDITY_VERSION_TO_STATE_LAYOUT.get(version)
        if not STATE_LAYOUT:
            logger.error('Invalid version', extra={'version': version})
            raise ValueError('Invalid version')
        return STATE_LAYOUT

    @staticmethod
    def getLayouts(version: int) -> dict:
        return {'state': Liquidity.getStateLayout(version)}

    @staticmethod
    def getAssociatedId(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'amm_associated_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getAssociatedAuthority(programId: Pubkey) -> Tuple[Pubkey, int]:
        return findProgramAddress(
            [bytes([97, 109, 109, 32, 97, 117, 116, 104, 111, 114, 105, 116, 121])],
            programId
        )

    @staticmethod
    def getAssociatedBaseVault(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'coin_vault_associated_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getAssociatedQuoteVault(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'pc_vault_associated_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getAssociatedLpMint(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'lp_mint_associated_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getAssociatedLpVault(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'temp_lp_token_associated_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getAssociatedTargetOrders(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'target_associated_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getAssociatedWithdrawQueue(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'withdraw_associated_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getAssociatedOpenOrders(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'open_order_associated_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getAssociatedConfigId(programId: Pubkey, marketId: Pubkey) -> Pubkey:
        public_key = findProgramAddress(
            [bytes(programId), bytes(marketId), b'amm_config_account_seed'],
            programId
        )['public_key']
        return public_key

    @staticmethod
    def getMarketAssociatedAuthority(program_id: Pubkey, market_id: Pubkey):
        seeds = [bytes(market_id)]

        nonce = 0
        public_key = None 

        while nonce < 100:
            try:
                seeds_with_nonce = seeds + [nonce.to_bytes(8, 'little')] + [b'\x00'] * 7
                public_key = Pubkey.find_program_address(seeds_with_nonce, program_id)
            except TypeError as err:
                raise err
            nonce += 1
            return public_key[0], nonce

        raise ValueError('Unable to find a viable program address nonce')

    @staticmethod
    def get_market_data(marketId: Pubkey):
        serumData = client.get_account_info(marketId, commitment='processed')
        data = serumData.value.data
        # print(data.hex())
        marketLpData = MARKET_LAYOUT.parse(data)
        vault_signer = Pubkey.create_program_address(
                [bytes(marketId), marketLpData.vault_signer_nonce.to_bytes(8, byteorder="little")],
                Pubkey.from_string(OPENBOOK)
            )
        # print(Pubkey.from_bytes(marketLpData.base_vault))
        # print(vault_signer)
        return marketLpData, vault_signer

    @staticmethod
    def getAssociatedPoolKeys(version: int, marketVersion: int, marketId: Pubkey, baseMint: Pubkey,
                              quoteMint: Pubkey, baseDecimals: int, quoteDecimals: int, programId: Pubkey,
                              marketProgramId: Pubkey):
        id = Liquidity.getAssociatedId(programId, marketId)
        lpMint = Liquidity.getAssociatedLpMint(programId, marketId)
        dict = Liquidity.getAssociatedAuthority(programId)
        authority = dict['public_key']
        nonce = dict['nonce']
        baseVault = Liquidity.getAssociatedBaseVault(programId, marketId)
        quoteVault = Liquidity.getAssociatedQuoteVault(programId, marketId)
        lpVault = Liquidity.getAssociatedLpVault(programId, marketId)
        openOrders = Liquidity.getAssociatedOpenOrders(programId, marketId)
        targetOrders = Liquidity.getAssociatedTargetOrders(programId, marketId)
        withdrawQueue = Liquidity.getAssociatedWithdrawQueue(programId, marketId)

        marketAuthority,market_nonce = Liquidity.getMarketAssociatedAuthority(marketProgramId, marketId)
        marketLpData, vaultSigner = Liquidity.get_market_data(marketId=marketId)

        return {
            'amm_id': str(id),
            'base_mint': str(baseMint),
            'quote_mint': str(quoteMint),
            'lp_mint': str(lpMint),
            'base_decimals': baseDecimals,
            'quote_decimals': quoteDecimals,
            'lp_decimals': baseDecimals,
            'version': version,
            'program_id': str(programId),
            'authority': str(authority),
            'nonce': nonce,
            'base_vault': str(baseVault),
            'quote_vault': str(quoteVault),
            'lp_vault': str(lpVault),
            'open_orders': str(openOrders),
            'target_orders': str(targetOrders),
            'withdraw_queue': str(withdrawQueue),
            'market_version': marketVersion,
            'market_program_id': str(marketProgramId),
            'market_id': str(marketId),
            'market_authority': str(marketAuthority),
            'valut_signer': str(vaultSigner),
            'market_base_vault': str(Pubkey.from_bytes(marketLpData.base_vault)),
            'market_quote_vault':str(Pubkey.from_bytes(marketLpData.quote_vault)),
            'bids':str(Pubkey.from_bytes(marketLpData.bids)),
            'asks':str(Pubkey.from_bytes(marketLpData.asks)),
            'event_queue':str(Pubkey.from_bytes(marketLpData.event_queue)),
            'lookup_table_account': str(Pubkey.default()),
            'config_id': str(Liquidity.getAssociatedConfigId(programId,marketId))
        }

# Additional methods for other associated components should be defined here, following the same pattern as above.