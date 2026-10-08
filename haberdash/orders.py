"""Order placement.

An order is a list of cart lines, each a SKU and a quantity. Placing it
looks every line up in the catalog, totals them, charges the card once for
the total and returns the order with its receipt.
"""

import uuid
from dataclasses import dataclass
from typing import Tuple

from haberdash.catalog import CatalogTimeout
from haberdash.payments import Receipt


class OrderError(Exception):
    """Base class for order placement errors."""


class CatalogUnavailable(OrderError):
    """The catalog could not be reached, so the order was not placed."""


class EmptyOrder(OrderError):
    """The cart had no lines."""


@dataclass(frozen=True)
class CartLine:
    sku: str
    quantity: int


@dataclass(frozen=True)
class OrderLine:
    sku: str
    name: str
    unit_price_cents: int
    quantity: int

    @property
    def total_cents(self):
        return self.unit_price_cents * self.quantity


@dataclass(frozen=True)
class Order:
    order_id: str
    lines: Tuple[OrderLine, ...]
    total_cents: int
    receipt: Receipt


def place_order(cart_lines, catalog, payments, card_token):
    """Place an order for ``cart_lines`` and charge ``card_token`` for it.

    Raises ``CatalogUnavailable`` if the catalog times out on any line,
    ``UnknownSku`` for a SKU the catalog does not know, and whatever the
    payment client raises if the charge fails.
    """
    if not cart_lines:
        raise EmptyOrder("an order needs at least one line")
    order_id = "ord_" + uuid.uuid4().hex[:12]
    lines = []
    for cart_line in cart_lines:
        if cart_line.quantity <= 0:
            raise ValueError(f"quantity for {cart_line.sku} must be positive")
        try:
            item = catalog.lookup(cart_line.sku)
        except CatalogTimeout as exc:
            raise CatalogUnavailable(
                f"catalog timed out looking up {cart_line.sku}"
            ) from exc
        lines.append(
            OrderLine(
                sku=item.sku,
                name=item.name,
                unit_price_cents=item.price_cents,
                quantity=cart_line.quantity,
            )
        )
    total_cents = sum(line.total_cents for line in lines)
    receipt = payments.charge(total_cents, card_token)
    return Order(
        order_id=order_id, lines=tuple(lines), total_cents=total_cents, receipt=receipt
    )
