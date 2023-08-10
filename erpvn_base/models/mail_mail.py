# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def _cron_send_email(self):
        seven_days_ago = fields.Datetime.now(self) + timedelta(days=-7)
        for mail in self.search([('date', '>=', seven_days_ago), ('state', 'in', ['outgoing', 'exception'])]):
            try:
                if mail.state == 'exception':
                    mail.mark_outgoing()
                mail.send()
            except MailDeliveryException as e:
                _logger.warning('MailDeliveryException while sending mail %d. Digest is now scheduled for next cron update.', mail.id)