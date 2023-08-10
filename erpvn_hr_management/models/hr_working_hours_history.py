# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrWorkingHourHistory(models.Model):
    _name = 'working.hour.history'
    _description = 'HR Working Hours History'
    _inherit = ['mail.thread']


    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Hours')
    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    responsible_id = fields.Many2one('res.users', string="Responsible")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    is_first = fields.Boolean(default = False)