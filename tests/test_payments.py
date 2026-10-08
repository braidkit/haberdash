import unittest

from haberdash.fakes import CHARGED_THEN_TIMEOUT, TIMEOUT
from haberdash.payments import PaymentTimeout, Receipt
from tests.support import CARD, make_clients


class PaymentClientTests(unittest.TestCase):
    def test_charge_records_one_charge(self):
        _, payments, _, payment_fake = make_clients()
        receipt = payments.charge(1250, CARD)
        self.assertEqual(receipt, Receipt(charge_id="ch_000001", amount_cents=1250))
        self.assertEqual(len(payment_fake.charges), 1)
        self.assertEqual(payment_fake.charges[0]["card_token"], CARD)

    def test_timeout_before_charge_records_nothing(self):
        _, payments, _, payment_fake = make_clients(payment_schedule=[TIMEOUT])
        with self.assertRaises(PaymentTimeout):
            payments.charge(1250, CARD)
        self.assertEqual(payment_fake.charges, [])

    def test_charged_then_timeout_records_the_charge(self):
        _, payments, _, payment_fake = make_clients(payment_schedule=[CHARGED_THEN_TIMEOUT])
        with self.assertRaises(PaymentTimeout):
            payments.charge(1250, CARD)
        self.assertEqual(len(payment_fake.charges), 1)
        self.assertEqual(payment_fake.charges[0]["amount_cents"], 1250)

    def test_idempotency_key_returns_same_receipt_without_second_charge(self):
        _, payments, _, payment_fake = make_clients()
        first = payments.charge(1250, CARD, idempotency_key="ord_abc123")
        second = payments.charge(1250, CARD, idempotency_key="ord_abc123")
        self.assertEqual(first, second)
        self.assertEqual(len(payment_fake.charges), 1)
        self.assertEqual(len(payment_fake.requests), 2)
