# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import models, fields, api, _

class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""
    _name = 'hr.employee.family'
    _description = 'HR Employee Family'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    phone_number = fields.Char(string='Contact No')
    birth_date = fields.Date(string="Birthday", tracking=True)
    age = fields.Float(compute="_compute_age")
    identification_id = fields.Char(string='Identification No', groups="hr.group_hr_user", tracking=True)
    address = fields.Char(string='Address')
    state_id = fields.Many2one("res.country.state", string='City/Province', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee")
    vat = fields.Char(string='Tax ID', index=True, help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee')
    notes = fields.Text('Notes', groups="hr.group_hr_user")

    @api.depends("birth_date")
    def _compute_age(self):
        for record in self:
            age = relativedelta(datetime.now(), record.birth_date)
            record.age = age.years + (age.months / 12)