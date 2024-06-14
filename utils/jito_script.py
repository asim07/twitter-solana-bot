
from typing import List

from solana.rpc.api import Client
from solana.rpc.commitment import Processed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solders.instruction import Instruction

from jito_searcher_client.generated.searcher_pb2 import GetTipAccountsRequest

from jito_searcher_client.convert import tx_to_protobuf_packet
from jito_searcher_client.generated.bundle_pb2 import Bundle
from jito_searcher_client.generated.searcher_pb2 import (
    SendBundleRequest
)
from jito_searcher_client.generated.searcher_pb2_grpc import SearcherServiceStub
from jito_searcher_client.generated.searcher_pb2 import SubscribeBundleResultsRequest
from jito_searcher_client.searcher import get_searcher_client

from utils.config import BLOCK_ENGINE_URL, JITO_PRIVATE_KEY

import random


def get_jito_client(block_engine_url, private_key):
    kp = Keypair.from_base58_string(private_key)
    return get_searcher_client(block_engine_url, kp)

last_used = None
key = "5q5BDPR38Y9hL6bhsP6UDB5N1B4myKhgVE9PZKT1xdFtnPQx751HZHApSEV5LqbwdoDcpgTNxNNFxNh27rgMiwmi"

client = get_jito_client(random.choice(BLOCK_ENGINE_URL), JITO_PRIVATE_KEY)


clients= [get_jito_client(random.choice(BLOCK_ENGINE_URL), JITO_PRIVATE_KEY)]

# print(client.GetTipAccounts(GetTipAccountsRequest()))
# print(Keypair.from_base58_string(JITO_PRIVATE_KEY).pubkey())

def send_bundle_txs_input(

    rpc_client: Client,
    payers: List[Keypair],
    txs: List[Transaction],
    lamports: int,
    tip_account: str,
):
    """
    Send a bundle!
    """
    
    tip_account = Pubkey.from_string(tip_account)
    blockhash = rpc_client.get_latest_blockhash().value.blockhash
    block_height = rpc_client.get_block_height(Processed).value

    
    
    tip_tx = Transaction(fee_payer=payers[0].pubkey(), instructions=[transfer(TransferParams(from_pubkey=payers[0].pubkey(), to_pubkey=tip_account, lamports=lamports))], recent_blockhash=blockhash)
    tip_tx.sign(payers[0])
    txs.append(tip_tx)
    print(txs)
    # Note: setting meta.size here is important so the block engine can deserialize the packet
    packets = [tx_to_protobuf_packet(tx) for tx in txs]
    clientt = random.choice(clients)
    uuid_response = clientt.SendBundle(SendBundleRequest(bundle=Bundle(header=None, packets=packets)))
    print(f"bundle uuid: {uuid_response.uuid}")
    return txs[0].signature()


def send_bundle(

    rpc_client: Client,
    payers: List[Keypair],
    instructions: List[Instruction],
    lamports: int,
    tip_account: str,
):
    """
    Send a bundle!
    """
    
    tip_account = Pubkey.from_string(tip_account)
    blockhash = rpc_client.get_latest_blockhash().value.blockhash
    block_height = rpc_client.get_block_height(Processed).value

    # Build bundle
    txs: List[Transaction] = []
    
    tx = Transaction(
        instructions=instructions, fee_payer=payers[0].pubkey(), recent_blockhash=blockhash
    )


    tx.sign(*payers)
    
    tip_tx = Transaction(fee_payer=payers[0].pubkey(), instructions=[transfer(TransferParams(from_pubkey=payers[0].pubkey(), to_pubkey=tip_account, lamports=lamports))], recent_blockhash=blockhash)
    tip_tx.sign(payers[0])
    
    print(f"signature={tx.signature()}")
    txs.append(tx)
    txs.append(tip_tx)

    # Note: setting meta.size here is important so the block engine can deserialize the packet
    packets = [tx_to_protobuf_packet(tx) for tx in txs]
    clientt = random.choice(clients)
    uuid_response = clientt.SendBundle(SendBundleRequest(bundle=Bundle(header=None, packets=packets)))
    print(f"bundle uuid: {uuid_response.uuid}")
    return tx.signature()

    # for tx in txs:
    #     print(
    #         rpc_client.confirm_transaction(
    #             tx.signatures[0], Processed, sleep_seconds=0.5, last_valid_block_height=block_height + 10
    #         )
    #     )