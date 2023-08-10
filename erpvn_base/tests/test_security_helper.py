import logging

from odoo.tests import common

_logger = logging.getLogger(__name__)


class SecurityTestCase(common.TransactionCase):
    def setUp(self):
        super(SecurityTestCase, self).setUp()
        self.model = self.env["res.partner"].with_user(
            self.browse_ref("base.user_admin")
        )
        self.record_ids = self.model.search([], limit=25).ids

    def tearDown(self):
        super(SecurityTestCase, self).tearDown()

    def test_check_access(self):
        self.model.browse(self.record_ids).check_access("read")
        self.model.browse(self.record_ids).check_access("create")
        self.model.browse(self.record_ids).check_access("write")
        self.model.browse(self.record_ids).check_access("unlink")

    def test_filter_access(self):
        self.model.browse(self.record_ids)._filter_access("read", in_memory=True)
        self.model.browse(self.record_ids)._filter_access("read", in_memory=False)
        self.model.browse(self.record_ids)._filter_access_ids("read", in_memory=True)
        self.model.browse(self.record_ids)._filter_access_ids("read", in_memory=False)
