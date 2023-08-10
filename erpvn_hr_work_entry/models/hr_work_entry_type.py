# -*- coding: utf-8 -*-
from odoo import models, _

class HrWorkEntryType(models.Model):
    _name = 'hr.work.entry.type'
    _inherit = ['hr.work.entry.type', 'mail.thread']

    