# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class OdooServerActionHistory(models.Model):
    _name = 'server.action.remote.history'
    _description = 'Server Action Remote History'

    server_id = fields.Many2one('server.action.remote')
    action = fields.Selection([
        ('started', 'Started'),
        ('stopped', 'Stopped'),
        ('restarted', 'Restarted'),
        ('pulled', 'Git Pulled'),
        ('backup_sql', 'Backup SQL'),
        ('backup_data', 'Backup Data'),
    ])

