import json
import logging

from odoo.addons.erpvn_utils.tools.json import RecordEncoder
from odoo.tests import common

_logger = logging.getLogger(__name__)


class JsonTestCase(common.TransactionCase):
    def test_json_dumps(self):
        record = self.env["ir.attachment"].search_read([], limit=1)
        json.dumps(record, sort_keys=True, indent=4, cls=RecordEncoder)
