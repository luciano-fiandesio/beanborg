"""Amount handling module for financial transactions.

This module provides functionality for converting various string representations
of monetary amounts into Decimal objects, handling different currency formats
and numerical notations.
"""

__copyright__ = "Copyright (C) 2024 Luciano Fiandesio"
__license__ = "GNU GPLv2"

from dataclasses import dataclass
from typing import Dict, Optional

from beancount.core.number import D, Decimal


@dataclass
class AmountConfig:
    """Configuration for amount handling.

    Attributes:
        indexes: Configuration for amount indexes
        rules: Rules for amount processing
    """

    class Indexes:
        """Indexes for amount processing."""
        amount_in: Optional[int]

    class Rules:
        """Rules for amount processing."""
        invert_negative: bool
        force_negative: int


class AmountHandler:
    """Handles conversion of string amounts to Decimal objects.

    This class provides functionality to convert various string representations
    of monetary amounts into Decimal objects, handling different currency formats
    and numerical notations.

    Attributes:
        SIGN_TRANS: Translation table for removing currency symbols and spaces
        DOT_TRANS: Translation table for removing thousands separators
    """

    # Translation tables for currency conversion
    SIGN_TRANS: Dict[str, str] = str.maketrans({"$": "", " ": ""})
    DOT_TRANS: Dict[str, str] = str.maketrans({".": "", ",": ""})

    def handle(self, val: str, args: AmountConfig) -> Decimal:
        """Process and convert an amount string based on configuration.

        Args:
            val: String representation of the amount
            args: Configuration for amount processing

        Returns:
            Decimal representation of the amount

        Example:
            >>> handler = AmountHandler()
            >>> handler.handle("$22,000.76", config)
            Decimal('22000.76')
        """
        if args.indexes.amount_in:
            return self._convert(val[args.indexes.amount_in].strip()) - self._convert(
                val
            )

        if args.rules.invert_negative and val[0] == "-":
            val = val.replace("-", "+")

        if args.rules.force_negative == 1 and val[0].isdigit():
            val = "-" + val

        return self._convert(val)

    def _convert(
        self,
        num: str,
        sign_trans: Dict[str, str] = SIGN_TRANS,
        dot_trans: Dict[str, str] = DOT_TRANS,
    ) -> Decimal:
        """Convert a string amount to a Decimal.

        Converts various string representations of amounts into Decimal objects,
        handling different formats and separators. The last two digits are always
        assumed to be decimals.

        Args:
            num: String representation of the amount
            sign_trans: Translation table for currency symbols
            dot_trans: Translation table for separators

        Returns:
            Decimal representation of the amount

        Examples:
            "22 000,76"      -> 22000.76
            "22.000,76"      -> 22000.76
            "22,000.76"      -> 22000.76
            "1022000,76"     -> 1022000.76
            "-1,022,000.76"  -> -1022000.76
            "1022000"        -> 1022000.0
            "22 000,76$"     -> 22000.76
            "$22 000,76"     -> 22000.76

        Raises:
            ValueError: If the string cannot be converted to a valid decimal
        """
        try:
            # Remove currency symbols and spaces
            num = num.translate(sign_trans)
            # Process the number, keeping last 3 chars (decimal point and 2 digits)
            num = num[:-3].translate(dot_trans) + num[-3:]
            # Convert to Decimal, replacing comma with decimal point
            return D(num.replace(",", "."))
        except (IndexError, ValueError) as e:
            raise ValueError(f"Invalid amount format: {num}") from e
