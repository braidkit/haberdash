import unittest

from haberdash.catalog import CatalogTimeout, Item, UnknownSku
from haberdash.fakes import OK, TIMEOUT
from tests.support import make_clients


class CatalogClientTests(unittest.TestCase):
    def test_lookup_returns_item(self):
        catalog, _, _, _ = make_clients()
        item = catalog.lookup("RIB-GRO-15-RED")
        self.assertEqual(item, Item("RIB-GRO-15-RED", "Grosgrain ribbon 15mm, red, per metre", 120))

    def test_unknown_sku(self):
        catalog, _, _, _ = make_clients()
        with self.assertRaises(UnknownSku):
            catalog.lookup("RIB-GRO-15-XXX")

    def test_slow_transport_raises_catalog_timeout(self):
        catalog, _, catalog_fake, _ = make_clients()
        catalog_fake.fail_next(1)
        with self.assertRaises(CatalogTimeout):
            catalog.lookup("THR-COT-40-BLK")

    def test_schedule_is_consumed_in_order(self):
        catalog, _, catalog_fake, _ = make_clients(catalog_schedule=[TIMEOUT, TIMEOUT, OK])
        for _ in range(2):
            with self.assertRaises(CatalogTimeout):
                catalog.lookup("THR-COT-40-BLK")
        self.assertEqual(catalog.lookup("THR-COT-40-BLK").price_cents, 395)
        self.assertEqual(catalog.lookup("THR-COT-40-BLK").price_cents, 395)
        self.assertEqual(len(catalog_fake.calls), 4)
