import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SOLANA_RPC = os.getenv("SOLANA_RPC")
WSS_SOLANA_RPC = os.getenv("SOLANA_RPC_WEBSOCKET")
SELL_TIME_SECONDS = float(os.getenv("SELL_TIME_SECONDS"))
MINT_AUTHORITY = True if os.getenv("MINT_AUTHORITY")=="True" else False
TARGET_TOKEN = os.getenv("TARGET_TOKEN_MINT")


LAMPORTS_PER_SOL = 1000000000
RAYDIUM_PUBLIC_KEY = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
TOKEN_PROGRAM_OWNER_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
RAYDIUM_AUTHORITY_V4 = "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"
OPEN_BOOK_SERUM = "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX"

TRANSFER_COMPUTE_PRICE = 15000
TRANSFER_COMPUTE_LIMIT = 100000

BLOCK_ENGINE_URL =  ["mainnet.block-engine.jito.wtf",
                     "amsterdam.mainnet.block-engine.jito.wtf",
                     "frankfurt.mainnet.block-engine.jito.wtf",
                     "ny.mainnet.block-engine.jito.wtf",
                     "tokyo.mainnet.block-engine.jito.wtf"


]
TIP_ACCOUNTS = ["96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
"HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
"Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
"ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
"DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
"ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
"DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
"3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"]
JITO_PRIVATE_KEY = "5SMXiRML4CweY3RbyZkj8RD2P7frT9Jk9iRZg1EQo21wbrLfYtmLZvvB9maYYz6da8xosrUKGfRpwvSLy476P78R"


SWAP_COMPUTE_PRICE = 1000000
SWAP_COMPUTE_LIMIT = 200000


# Compute Unit Price in Micro Lamports
COMPUTE_PRICE = 200000000
COMPUTE_LIMIT = 200000





BOT_TOKEN = "7083446719:AAGShxImD-pCT7YDl9213CuqW3I1zUPCXqM"