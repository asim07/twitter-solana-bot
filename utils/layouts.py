from construct import Bytes, Int8ul, Int64ul, BytesInteger , Padding, Int32ul
from construct import Struct as cStruct
from construct import BitsInteger, BitsSwapped, BitStruct, Const, Flag

PUBLIC_KEY_LAYOUT = Bytes(32)
# We will use a bitstruct with 64 bits instead of the widebits implementation in serum-js.
ACCOUNT_FLAGS_LAYOUT = BitsSwapped(  # Swap to little endian
    BitStruct(
        "initialized" / Flag,
        "market" / Flag,
        "open_orders" / Flag,
        "request_queue" / Flag,
        "event_queue" / Flag,
        "bids" / Flag,
        "asks" / Flag,
        Const(0, BitsInteger(57)),  # Padding
    )
)

MINT_LAYOUT = cStruct(
    "mint_authority_option" / Int32ul,
    "mint_authority" / PUBLIC_KEY_LAYOUT,
    "supply" / Int64ul,
    "decimals" / Int8ul,
    "is_initialized" / Int8ul,
    "freeze_authority_option" / Int32ul,
    "freeze_authority" / PUBLIC_KEY_LAYOUT,
)

# Not in use right now, might be useful in future
AMM_INFO_LAYOUT_V4 = cStruct(
    'status' / Int64ul,
    'nonce' / Int64ul,
    'order_num' / Int64ul,
    'depth' / Int64ul,
    'base_decimal' / Int64ul,
    'quote_decimal' / Int64ul,
    'state' / Int64ul,
    'reset_flag' / Int64ul,
    'min_size' / Int64ul,
    'vol_max_cut_ratio' / Int64ul,
    'amount_wave_ratio' / Int64ul,
    'base_lot_size' / Int64ul,
    'quote_lot_size' / Int64ul,
    'min_price_multiplier' / Int64ul,
    'max_price_multiplier' / Int64ul,
    'system_decimal_value' / Int64ul,
    # Fees
    'min_separate_numerator' / Int64ul,
    'min_separate_denominator' / Int64ul,
    'trade_fee_numerator' / Int64ul,
    'trade_fee_denominator' / Int64ul,
    'pnl_numerator' / Int64ul,
    'pnl_denominator' / Int64ul,
    'swap_fee_numerator' / Int64ul,
    'swap_fee_denominator' / Int64ul,
    # OutPutData
    'base_need_take_pnl' / Int64ul,
    'quote_need_take_pnl' / Int64ul,
    'quote_total_pnl' / Int64ul,
    'base_total_pnl' / Int64ul,
    # 128
    'quote_total_deposited' / BytesInteger(16, signed=False, swapped=True),
    'base_total_deposited' / BytesInteger(16, signed=False, swapped=True),
    'swap_base_in_amount' / BytesInteger(16, signed=False, swapped=True),
    'swap_quote_out_amount' / BytesInteger(16, signed=False, swapped=True),

    'swap_base2_quote_fee' / Int64ul,
    # 128
    'swap_quote_in_amount' / BytesInteger(16, signed=False, swapped=True),
    'swap_base_out_amount' / BytesInteger(16, signed=False, swapped=True),

    'swap_quote2_base_fee' / Int64ul,
    # AMM Vault
    'base_vault' / Bytes(32),
    'quote_vault' / Bytes(32),
    # Mint
    'base_mint' / Bytes(32),
    'quote_mint' / Bytes(32),
    'lp_mint' / Bytes(32),
    # Market
    'open_orders' / Bytes(32),
    'market_id' / Bytes(32),
    'serum_program_id' / Bytes(32),
    'target_orders' / Bytes(32),
    'withdraw_queue' / Bytes(32),
    'lp_vault' / Bytes(32),
    'amm_owner' / Bytes(32),

    'lpReserve' / Int64ul,
)

MARKET_LAYOUT = cStruct(
    Padding(5),
    "account_flags" / ACCOUNT_FLAGS_LAYOUT,
    "own_address" / Bytes(32),
    "vault_signer_nonce" / Int64ul,
    "base_mint" / Bytes(32),
    "quote_mint" / Bytes(32),
    "base_vault" / Bytes(32),
    "base_deposits_total" / Int64ul,
    "base_fees_accrued" / Int64ul,
    "quote_vault" / Bytes(32),
    "quote_deposits_total" / Int64ul,
    "quote_fees_accrued" / Int64ul,
    "quote_dust_threshold" / Int64ul,
    "request_queue" / Bytes(32),
    "event_queue" / Bytes(32),
    "bids" / Bytes(32),
    "asks" / Bytes(32),
    "base_lot_size" / Int64ul,
    "quote_lot_size" / Int64ul,
    "fee_rate_bps" / Int64ul,
    "referrer_rebate_accrued" / Int64ul,
    Padding(7),
)

POOL_INFO_LAYOUT = cStruct(
    "instruction" / Int8ul,
    "simulate_type" / Int8ul
)

SWAP_LAYOUT = cStruct(
    "instruction" / Int8ul,
    "amount_in" / Int64ul,
    "min_amount_out" / Int64ul
)