"""In-memory transports for the catalog and payment services.

Both fakes take a ``schedule``: a list of outcomes consumed one per call,
so a test can say "time out twice, then answer normally". Once the schedule
runs out every call succeeds. ``fail_next(n)`` prepends ``n`` timeouts.
"""

OK = "ok"
TIMEOUT = "timeout"
# Payment only: the provider makes the charge but the response is lost.
CHARGED_THEN_TIMEOUT = "charged-then-timeout"


class FakeCatalogTransport:
    """Serves a fixed set of items the way the catalog service would."""

    def __init__(self, items, schedule=None):
        self._items = {item.sku: item for item in items}
        self.schedule = list(schedule or [])
        self.calls = []

    def fail_next(self, count):
        self.schedule = [TIMEOUT] * count + self.schedule

    def get(self, path, timeout):
        self.calls.append(path)
        outcome = self.schedule.pop(0) if self.schedule else OK
        if outcome == TIMEOUT:
            raise TimeoutError(path)
        item = self._items.get(path.rsplit("/", 1)[-1])
        if item is None:
            return None
        return {"sku": item.sku, "name": item.name, "price_cents": item.price_cents}


class FakePaymentTransport:
    """Behaves like the payment provider, including its idempotency keys.

    ``charges`` lists every charge the provider actually made, one entry per
    charge, whether or not the caller ever saw the response. ``requests``
    lists every request body received.
    """

    def __init__(self, schedule=None):
        self.schedule = list(schedule or [])
        self.charges = []
        self.requests = []
        self._by_key = {}

    def fail_next(self, count):
        self.schedule = [TIMEOUT] * count + self.schedule

    def post(self, path, body, headers, timeout):
        self.requests.append(dict(body))
        outcome = self.schedule.pop(0) if self.schedule else OK
        if outcome == TIMEOUT:
            raise TimeoutError(path)
        key = headers.get("Idempotency-Key")
        if key is not None and key in self._by_key:
            charge = self._by_key[key]
        else:
            charge = {
                "charge_id": f"ch_{len(self.charges) + 1:06d}",
                "amount_cents": body["amount_cents"],
                "card_token": body["card_token"],
                "status": "succeeded",
            }
            self.charges.append(charge)
            if key is not None:
                self._by_key[key] = charge
        if outcome == CHARGED_THEN_TIMEOUT:
            raise TimeoutError(path)
        return dict(charge)
