import logging

from odoo.tests import common

_logger = logging.getLogger(__name__)


class SearchChildsTestCase(common.TransactionCase):
    def setUp(self):
        super(SearchChildsTestCase, self).setUp()
        self.model = self.env["res.partner.category"]
        self.parent = self.model.create(
            {"parent_id": False, "name": "Parent", "active": True}
        )
        self.child = self.model.create(
            {"parent_id": self.parent.id, "name": "Child", "active": True}
        )
        self.child_parent = self.model.create(
            {"parent_id": self.parent.id, "name": "Child Parent", "active": True}
        )
        self.child_parent_child = self.model.create(
            {
                "parent_id": self.child_parent.id,
                "name": "Child Parent Child",
                "active": True,
            }
        )

    def tearDown(self):
        super(SearchChildsTestCase, self).tearDown()

    def test_search_childs(self):
        childs = self.model.search_childs(self.parent.id)
        self.assertEqual(set(childs.ids), {self.child.id, self.child_parent.id})

    def test_search_read_childs(self):
        childs = self.model.search_childs(self.parent.id)
        childs_names = self.model.search_read_childs(self.parent.id, fields=["name"])
        self.assertEqual(childs.read(["name"]), childs_names)
