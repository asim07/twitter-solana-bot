import requests, json
from utils.config import WSS_SOLANA_RPC

def check_for_market_id(token):
    data = {"jsonrpc":"2.0", 
        "id":1, 
        "method":"getProgramAccounts", 
        "params":[
            "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX",
            {
                "filters":
                [
                    {
                      "memcmp": {
                        "offset": 53,
                        "bytes": token
                      }
                    },
                    {
                      "memcmp": {
                        "offset": 85,
                        "bytes": 'So11111111111111111111111111111111111111112'
                      }
                    },
                    
                ],
            
                "encoding": "base64"
            }
  ]}
    try:
        response = requests.post(WSS_SOLANA_RPC.replace('wss','https'), json=data)
        resp = (json.loads(response.text))
        
        return resp['result'][0]['pubkey']
    except Exception as e:
        print(e)
        return None