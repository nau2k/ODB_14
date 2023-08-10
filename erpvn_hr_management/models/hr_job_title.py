# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrJobTitle(models.Model):
    _name = 'hr.job.title'
    _description = 'HR Job Title'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string='Active', default=True)
    code = fields.Char(string='Code', help="Job Title Code")
    name = fields.Char(string='Title Name', help="Title Name", required=True, translate=True)
    job_id = fields.Many2one(string='Job Position', comodel_name='hr.job', ondelete='restrict',)
    department_id = fields.Many2one(string='Department', comodel_name='hr.department',)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)