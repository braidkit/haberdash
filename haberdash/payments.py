"""Client for the payment provider.

The provider supports idempotency keys. A charge request that carries a key
is processed at most once: a repeat request with the same key returns the
original receipt instead of charging the card a second time.

A timeout does not mean the charge failed. The provider may have charged the
card and the response was lost on the way back, so after a
``PaymentTimeout`` the outcome of that charge is unknown.
"""

from dataclasses import dataclass


class PaymentError(Exception):
    """Base class for payment client errors."""


class PaymentTimeout(PaymentError):
    """The provider did not answer before the request deadline."""


class PaymentDeclined(PaymentError):
    """The provider refused to charge the card."""


@dataclass(frozen=True)
class Receipt:
    charge_id: str
    amount_cents: int


class PaymentClient:
    """Charges cards through the payment provider.

    ``transport`` is any object with ``post(path, body, headers, timeout)``
    that returns the decoded response body or raises ``TimeoutError`` when
    the deadline passes.
    """

    def __init__(self, transport, timeout=2.0):
        self._transport = transport
        self._timeout = timeout

    def charge(self, amount_cents, card_token, idempotency_key=None):
        """Charge ``amount_cents`` to the card behind ``card_token``.

        ``idempotency_key``, when given, is sent to the provider so that a
        repeated request with the same key returns the original receipt
        rather than making a second charge.
        """
        if amount_cents <= 0:
            raise ValueError(f"charge amount must be positive, got {amount_cents}")
        body = {"amount_cents": amount_cents, "card_token": card_token}
        headers = {}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        try:
            payload = self._transport.post(
                "/charges", body, headers=headers, timeout=self._timeout
            )
        except TimeoutError as exc:
            raise PaymentTimeout(
                f"charge of {amount_cents} cents timed out after {self._timeout}s"
            ) from exc
        if payload.get("status") == "declined":
            raise PaymentDeclined(payload.get("reason", "card declined"))
        return Receipt(
            charge_id=payload["charge_id"], amount_cents=int(payload["amount_cents"])
        )
