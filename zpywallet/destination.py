from decimal import Decimal, InvalidOperation

from enum import Enum
from .utils.keys import PublicKey


class FeePolicy(Enum):
    """
    Enumeration representing fee policies.

    FeePolicy.NONE: Indicates no fee policy.
    FeePolicy.PROPORTIONAL: Indicates a proportional fee policy.
    """

    NONE = 0
    PROPORTIONAL = 1


class Destination:
    """
    Represents a destination address and amount to send.
    """

    def __init__(
        self,
        address,
        amount,
        network,
        fee_policy=FeePolicy.NONE,
        in_standard_units=True,
    ):
        """
        Initializes a Destination object.

        Args:
            address (str): The destination address.
            amount (int): The amount of the destination.
            network: The network associated with the destination.
            fee_policy (FeePolicy, optional): The fee policy associated with the destination.
                Defaults to FeePolicy.NONE.
            in_standard_units (bool, optional): If True, `amount` is in BTC/ETH-style
                standard units. If False, `amount` is already in sats/wei.
        """
        self._network = network
        self._address = address
        self._fee_policy = fee_policy
        self._unit = 10**18 if network.SUPPORTS_EVM else 10**8
        self._amount_raw = self._normalize_amount(amount, in_standard_units)
        self._script_pubkey = PublicKey.address_script(address, network)

    @staticmethod
    def _coerce_decimal(amount):
        if isinstance(amount, Decimal):
            return amount
        try:
            return Decimal(str(amount))
        except (InvalidOperation, ValueError, TypeError) as e:
            raise TypeError("Amount must be numeric") from e

    def _normalize_amount(self, amount, in_standard_units):
        decimal_amount = self._coerce_decimal(amount)
        scaled = (
            decimal_amount * self._unit if in_standard_units else decimal_amount
        )
        if scaled != scaled.to_integral_value():
            unit_name = "wei" if self._network.SUPPORTS_EVM else "satoshis"
            raise ValueError(
                f"Amount cannot be represented exactly in {unit_name}"
            )

        amount_raw = int(scaled)
        if amount_raw < 0:
            raise ValueError("Amount must be non-negative")
        return amount_raw

    def address(self):
        """
        Returns the destination address.
        """
        return self._address

    def amount(self, in_standard_units=True):
        """
        Returns the amount of the destination.

        Args:
            in_standard_units (bool, optional): If True, returns the amount in standard units.
                If False, returns the amount in the lowest denomination. Defaults to True.
        """
        if not in_standard_units:
            return self._amount_raw
        return self._amount_raw / self._unit

    def fee_policy(self):
        """
        Returns the fee policy associated with the destination.
        """
        return self._fee_policy

    def script_pubkey(self):
        """
        Returns the script public key associated with the destination.
        """
        return self._script_pubkey
