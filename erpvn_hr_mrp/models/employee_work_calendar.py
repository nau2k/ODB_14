# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class EmployeeWorkCalendar(models.Model):
    _name = 'employee.work.calendar'
    _description = "Employee Work Calendar"

    name = fields.Char('Reason')
    company_id = fields.Many2one('res.company', related='calendar_id.company_id', string="Company",
        readonly=True, store=True)
    calendar_id = fields.Many2one('resource.calendar', 'Working Hours', index=True)
    date_from = fields.Datetime('Start Date', required=True)
    date_to = fields.Datetime('End Date', required=True)
    resource_id = fields.Many2one("resource.resource", 'Resource', index=True)
    production_id = fields.Many2one('mrp.production', 'Manufacturing Order', check_company=True, readonly=True)
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order', check_company=True, readonly=True)
    employee_id = fields.Many2one(string='WorkCenter', comodel_name='hr.employee')