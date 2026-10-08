"""Shared fixtures for the test suite."""

from haberdash.catalog import CatalogClient, Item
from haberdash.fakes import FakeCatalogTransport, FakePaymentTransport
from haberdash.payments import PaymentClient

ITEMS = [
    Item("THR-COT-40-BLK", "Cotton thread 40wt, black, 500m", 395),
    Item("RIB-GRO-15-RED", "Grosgrain ribbon 15mm, red, per metre", 120),
    Item("BRD-SOU-06-GLD", "Soutache braid 6mm, gold, per metre", 210),
    Item("BTN-SHL-18-NAT", "Shell buttons 18mm, natural, card of 6", 480),
]

CARD = "tok_visa_4242"


def make_clients(catalog_schedule=None, payment_schedule=None):
    """Return (catalog_client, payment_client, catalog_fake, payment_fake)."""
    catalog_fake = FakeCatalogTransport(ITEMS, schedule=catalog_schedule)
    payment_fake = FakePaymentTransport(schedule=payment_schedule)
    return (
        CatalogClient(catalog_fake),
        PaymentClient(payment_fake),
        catalog_fake,
        payment_fake,
    )
