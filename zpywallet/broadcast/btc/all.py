import asyncio
import binascii
import hashlib
from .bitaps import *
from .blockchain_info import *
from .blockchair import *
from .blockcypher import *
from .blockstream import *
from .coinify import *
from .esplora import *
from .f2pool import *
from .fullnode import *
from .mempool_space import *
from .smartbit import *
from .viabtc import *

def tx_hash_btc(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

async def broadcast_transaction_btc(raw_transaction_hex: bytes, rpc_nodes=[], esplora_nodes=[]):
    raw_transaction_hex = raw_transaction_hex.decode()
    tasks = []

    tasks.append(asyncio.create_task(broadcast_transaction_btc_bitaps(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_blockchain_info(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_blockchair(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_blockcypher(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_blockstream(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_coinify(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_f2pool(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_mempool_space(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_smartbit(raw_transaction_hex)))
    tasks.append(asyncio.create_task(broadcast_transaction_btc_viabtc(raw_transaction_hex)))
    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_btc_full_node(raw_transaction_hex, node)))
    for node in esplora_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_btc_esplora(raw_transaction_hex, node)))
    
    await asyncio.gather(*tasks, return_exceptions=True)
    