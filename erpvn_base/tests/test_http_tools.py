import base64
import logging

from odoo.addons.erpvn_utils.tools import http
from odoo.tests import common

_logger = logging.getLogger(__name__)


class HttpTestCase(common.TransactionCase):
    def test_decode_http_basic_authentication(self):
        credentials = base64.b64encode(b"username:password").decode("ascii")
        res = http.decode_http_basic_authentication("Basic {}".format(credentials))
        self.assertEqual(res, ("username", "password"))
