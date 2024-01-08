import asyncio
import binascii
import hashlib
from .fullnode import *

def tx_hash_dashtest(raw_transaction_hex):
    return binascii.hexlify(hashlib.sha256(hashlib.sha256(raw_transaction_hex).digest()).digest())

async def broadcast_transaction_dashtest(raw_transaction_hex: bytes, rpc_nodes=[]):
    raw_transaction_hex = raw_transaction_hex.decode()
    tasks = []

    for node in rpc_nodes:
        tasks.append(asyncio.create_task(broadcast_transaction_dashtest_full_node(raw_transaction_hex, node)))
    
    await asyncio.gather(*tasks, return_exceptions=True)