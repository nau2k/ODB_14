import logging

from odoo.osv import expression
from odoo.tests import common

_logger = logging.getLogger(__name__)


class MigrationTestCase(common.TransactionCase):
    def setUp(self):
        super(MigrationTestCase, self).setUp()
        self.model = self.env["ir.attachment"]
        self.params = self.env["ir.config_parameter"].sudo()
        self.location = self.params.get_param("ir_attachment.location")
        if self.location == "file":
            self.params.set_param("ir_attachment.location", "db")
        else:
            self.params.set_param("ir_attachment.location", "file")

    def tearDown(self):
        self.params.set_param("ir_attachment.location", self.location)
        super(MigrationTestCase, self).tearDown()

    def test_storage_domain(self):
        self.assertEqual(
            self.model._get_storage_domain("db"), [("db_datas", "=", False)]
        )
        self.assertEqual(
            self.model._get_storage_domain("file"), [("store_fname", "=", False)]
        )

    def test_force_storage_domain(self):
        force_storage_domain = expression.AND(
            [
                self.model._get_storage_domain("db"),
                [
                    "&",
                    "|",
                    ("res_field", "=", False),
                    ("res_field", "!=", False),
                    ("type", "=", "binary"),
                ],
            ]
        )
        self.assertFalse(expression.is_false(self.model, force_storage_domain))

    def test_migration(self):
        self.model.search([("type", "=", "binary")], limit=25).migrate()
