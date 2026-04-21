from .blockcypher import broadcast_transaction_eth_blockcypher
from .fullnode import broadcast_transaction_eth_generic
from .mew import broadcast_transaction_eth_mew
from ._helpers import normalize_raw_transaction as _normalize_raw_transaction
from ._helpers import tx_hash_eth
from ...nodes.eth import eth_nodes
from ...nodes.ethsepolia import ethsepolia_nodes
from .._parallel import gather_broadcast_tasks


async def broadcast_transaction_eth(raw_transaction_hex, **kwargs):
    """Broadcast a Ethereum transaction.

    This function attempts to asynchronously broadcast a signed transaction to
    several propagators that relay the transaction across the network.

    It can also be used to broadcast the transaction of any kind of EVM token.

    Args:
        raw_transaction_hex (str): The raw transaction in hexadecimal form.
    """

    normalized_transaction = _normalize_raw_transaction(raw_transaction_hex)
    rpc_nodes = kwargs.get("rpc_nodes") or kwargs.get("fullnode_endpoints") or []
    network = kwargs.get("network")
    stock_nodes = eth_nodes
    if getattr(network, "CHAIN", None) == "sepolia":
        stock_nodes = ethsepolia_nodes

    awaitables = []
    if getattr(network, "CHAIN", "main") == "main":
        awaitables.extend(
            [
                broadcast_transaction_eth_blockcypher(normalized_transaction),
                broadcast_transaction_eth_mew(normalized_transaction),
            ]
        )
    for node in rpc_nodes:
        awaitables.append(
            broadcast_transaction_eth_generic(normalized_transaction, **node)
        )
    for node in stock_nodes:
        awaitables.append(
            broadcast_transaction_eth_generic(normalized_transaction, **node)
        )

    return await gather_broadcast_tasks(awaitables)
