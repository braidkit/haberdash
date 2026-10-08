import unittest

from haberdash.fakes import CHARGED_THEN_TIMEOUT, TIMEOUT
from haberdash.orders import CartLine, CatalogUnavailable, place_order
from haberdash.payments import PaymentTimeout
from tests.support import CARD, make_clients

CART = [
    CartLine("THR-COT-40-BLK", 2),
    CartLine("RIB-GRO-15-RED", 5),
    CartLine("BTN-SHL-18-NAT", 1),
]
CART_TOTAL = 2 * 395 + 5 * 120 + 480


class PlaceOrderTests(unittest.TestCase):
    def test_happy_path_totals_lines_and_charges_once(self):
        catalog, payments, _, payment_fake = make_clients()
        order = place_order(CART, catalog, payments, CARD)
        self.assertEqual(order.total_cents, CART_TOTAL)
        self.assertEqual([line.sku for line in order.lines], [line.sku for line in CART])
        self.assertEqual(order.lines[1].name, "Grosgrain ribbon 15mm, red, per metre")
        self.assertEqual(order.receipt.amount_cents, CART_TOTAL)
        self.assertEqual(len(payment_fake.charges), 1)
        self.assertTrue(order.order_id.startswith("ord_"))

    def test_catalog_timeout_fails_the_order_without_charging(self):
        catalog, payments, catalog_fake, payment_fake = make_clients()
        catalog_fake.fail_next(1)
        with self.assertRaises(CatalogUnavailable):
            place_order(CART, catalog, payments, CARD)
        self.assertEqual(payment_fake.charges, [])

    def test_payment_timeout_surfaces(self):
        catalog, payments, _, _ = make_clients(payment_schedule=[TIMEOUT])
        with self.assertRaises(PaymentTimeout):
            place_order(CART, catalog, payments, CARD)

    def test_lost_charge_response_surfaces_as_timeout(self):
        catalog, payments, _, payment_fake = make_clients(payment_schedule=[CHARGED_THEN_TIMEOUT])
        with self.assertRaises(PaymentTimeout):
            place_order(CART, catalog, payments, CARD)
        self.assertEqual(len(payment_fake.charges), 1)
