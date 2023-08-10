# -*- coding: utf-8 -*-
from odoo import models, fields, _

class HRJob(models.Model):
    _inherit = 'hr.job'

    effective_percent = fields.Float("Effective Percent (%)", default=100)