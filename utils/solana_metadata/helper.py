import requests
import json
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from solders.signature import Signature
import base64
import base58
import struct
from construct import Bytes, Flag, Int8ul
from construct import Struct as cStruct  # type: ignore
from utils.config import SOLANA_RPC



client = Client(SOLANA_RPC, commitment='processed')

METADATA_PROGRAM_ID = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
def get_metadata_account(mint_key):
    return Pubkey.find_program_address(
        [b'metadata', bytes(METADATA_PROGRAM_ID), bytes(Pubkey.from_string(mint_key))],
        METADATA_PROGRAM_ID
    )[0]

def unpack_metadata_account(data):
    assert(data[0] == 4)
    i = 1
    source_account = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
    i += 32
    mint_account = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
    i += 32
    name_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4
    name = struct.unpack('<' + "B"*name_len, data[i:i+name_len])
    i += name_len
    symbol_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4 
    symbol = struct.unpack('<' + "B"*symbol_len, data[i:i+symbol_len])
    i += symbol_len
    uri_len = struct.unpack('<I', data[i:i+4])[0]
    i += 4 
    uri = struct.unpack('<' + "B"*uri_len, data[i:i+uri_len])
    i += uri_len
    fee = struct.unpack('<h', data[i:i+2])[0]
    i += 2
    has_creator = data[i] 
    i += 1
    creators = []
    verified = []
    share = []
    if has_creator:
        creator_len = struct.unpack('<I', data[i:i+4])[0]
        i += 4
        for _ in range(creator_len):
            creator = base58.b58encode(bytes(struct.unpack('<' + "B"*32, data[i:i+32])))
            creators.append(creator)
            i += 32
            verified.append(data[i])
            i += 1
            share.append(data[i])
            i += 1
    primary_sale_happened = bool(data[i])
    i += 1
    is_mutable = bool(data[i])
    metadata = {
        "update_authority": source_account,
        "mint": mint_account,
        "data": {
            "name": bytes(name).decode("utf-8").strip("\x00"),
            "symbol": bytes(symbol).decode("utf-8").strip("\x00"),
            "uri": bytes(uri).decode("utf-8").strip("\x00"),
            "seller_fee_basis_points": fee,
            "creators": creators,
            "verified": verified,
            "share": share,
        },
        "primary_sale_happened": primary_sale_happened,
        "is_mutable": is_mutable,
    }
    return metadata

def fetch_metadata(client, mint_key):
    metadata_account = get_metadata_account(mint_key)
    data = client.get_account_info(metadata_account).value
    if data:
        data = data.data
    else:
        return {"name": "-", "symbol": "-"}

    # data = base64.b64decode(client.get_account_info(metadata_account).value.data)
    metadata = unpack_metadata_account(data)
    return metadata


def get_metadata(mint_id):
	retries = 0
	while retries < 3:
		retries += 1
		try:
			data = fetch_metadata(client, mint_id)['data']
			return data
		except Exception as e:
			print(f"Error getting metadata for NFT: {mint_id}, trying again now... Error: {str(e)}")
			continue
	print(f"Error getting metadata for NFT: {mint_id} after max retries, giving up!")
	return {"name": "NA", "symbol": "-"}