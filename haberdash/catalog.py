"""Client for the catalog service.

The catalog service owns the SKU list for the shop: every spool of thread,
reel of ribbon, card of braid and box of buttons we stock, with its current
name and price. Orders look each line up here before charging the card.
"""

from dataclasses import dataclass


class CatalogError(Exception):
    """Base class for catalog client errors."""


class CatalogTimeout(CatalogError):
    """The catalog service did not answer before the request deadline."""


class UnknownSku(CatalogError):
    """The catalog has no item with the requested SKU."""


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    price_cents: int


class CatalogClient:
    """Looks items up in the catalog service.

    ``transport`` is any object with ``get(path, timeout)`` that returns the
    decoded response body (``None`` for a missing item) or raises
    ``TimeoutError`` when the deadline passes. Production uses
    ``HttpTransport``; the tests use an in-memory transport.
    """

    def __init__(self, transport, timeout=0.5):
        self._transport = transport
        self._timeout = timeout

    def lookup(self, sku):
        """Return the ``Item`` for ``sku``.

        Raises ``UnknownSku`` if the catalog has no such item and
        ``CatalogTimeout`` if the service does not answer in time.
        """
        try:
            payload = self._transport.get("/items/" + sku, timeout=self._timeout)
        except TimeoutError as exc:
            raise CatalogTimeout(
                f"catalog lookup for {sku} timed out after {self._timeout}s"
            ) from exc
        if payload is None:
            raise UnknownSku(sku)
        return Item(
            sku=payload["sku"],
            name=payload["name"],
            price_cents=int(payload["price_cents"]),
        )
