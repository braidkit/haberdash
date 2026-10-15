# Orders fail when the catalog service times out

Placing an order looks up each line item in the catalog service, then charges
the card through the payment service. The catalog service has been timing out
a few times an hour, and every timeout fails the whole order with
`CatalogUnavailable`.

Add retries so a brief catalog blip doesn't fail the order.

- Timeouts are short-lived. A retry a moment later almost always succeeds, so a
  small, bounded number of retries is enough.
- Payment timeouts can happen after the card was charged (see the payment
  client). An order must never charge a card twice.

Keep the tests green and add coverage: a timeout that recovers, retries that
run out, and a charge made at most once.
