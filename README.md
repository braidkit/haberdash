# Haberdash

Haberdash is the order service for a small haberdashery that sells thread,
ribbon, braid and buttons. It looks each cart line up in the catalog service,
totals the order and charges the card through the payment provider.

It needs Python 3.9 or newer and nothing outside the standard library.

## Running the tests

```bash
python3 -m unittest
```

The tests run against in-memory transports in `haberdash/fakes.py`, so no
services need to be up.

## Usage

```python
from haberdash import CartLine, CatalogClient, PaymentClient, place_order
from haberdash.transport import HttpTransport

catalog = CatalogClient(HttpTransport("https://catalog.internal"))
payments = PaymentClient(HttpTransport("https://payments.example.com/v1"))

order = place_order(
    [CartLine("THR-COT-40-BLK", 2), CartLine("RIB-GRO-15-RED", 5)],
    catalog,
    payments,
    card_token="tok_visa_4242",
)
print(order.order_id, order.total_cents, order.receipt.charge_id)
```

## Issue #1

**Orders fail when the catalog service times out**

Placing an order looks up each line item in the catalog service, then charges
the card through the payment service. The catalog service has been timing out
a few times an hour, and every timeout fails the whole order with
`CatalogUnavailable`.

Add retries so a brief catalog blip doesn't fail the order. Keep the tests
green and add coverage for the retry behaviour.

Notes from on-call:

- Timeouts are short-lived. A retry a moment later almost always succeeds.
- We had one report last month of a customer charged twice. Probably
  unrelated, nobody has looked.

## License

MIT, see [LICENSE](LICENSE).
