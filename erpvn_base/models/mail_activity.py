# -*- coding: utf-8 -*-
from odoo import models, _

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def action_notify(self):
        if not self:
            return

        for activity in self.filtered(lambda x: x.user_id):
            activity.user_id = self.sudo().env['res.users'].browse(1)

        return super(MailActivity, self).action_notify()
