# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class MessageWizard(models.TransientModel):
    _name = 'message.wizard'
    _description = 'Message Wizard'

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    message = fields.Text('Message',default = get_default)

    def action_ok(self):
        """ close wizard"""
        return {'type': 'ir.actions.act_window_close'}