# -*- coding: utf-8 -*-
from odoo import models, fields, api,_


class HRJob(models.Model):
    _inherit='hr.job'

    title_ids = fields.One2many(string='Jobs', comodel_name='hr.job.title', inverse_name='job_id',)