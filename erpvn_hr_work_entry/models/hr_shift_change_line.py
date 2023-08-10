# -*- coding: utf-8 -*-
from pytz import UTC
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from datetimerange import DateTimeRange

class HRShiftChangeLine(models.Model):
    _name = 'hr.shift.change.line'
    _order = 'id desc'
    _description = "HR Shift Change Line"
    _inherit = 'mail.thread'

    sequence = fields.Integer(default=1, index=True)
    name = fields.Char('Name')
    order_id = fields.Many2one('hr.shift.change.order', 'Order', ondelete='cascade', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    employee_code = fields.Char(related='employee_id.barcode', string='Barcode',store=True)
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id", store=True)
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id", store=True)
    manager_id = fields.Many2one('res.users', string='Manager')

    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Shift', tracking=True)
    attendance_id = fields.Many2one('resource.calendar.attendance', string='Work Detail', tracking=True)
    date_from = fields.Datetime(string='From', tracking=True)
    date_to = fields.Datetime(string='To', tracking=True)
    duration = fields.Float(string='Duration', store=True, compute='_compute_duration')
    break_time = fields.Float(string='Break Time', store=True, compute='_compute_duration')

    work_entry_id = fields.Many2one('hr.work.entry', string='Work Entry', tracking=True)
    status = fields.Selection([
        ('validation', 'Validation'), 
        ('duplicated-request', 'Duplicated Request'), 
        ('validated-shift', 'Shift Has Validated')], string="Status", default="validation")
    state = fields.Selection(related='order_id.state', string='State', store=True)
    note = fields.Text('Note')

    @api.onchange('employee_id', 'date_from', 'date_to')
    def _check_line_status(self):
        for line in self:
            if not (line.employee_id and line.date_from and line.date_to):
                continue

            line.status = line._check_status()

    def _check_status(self):
        self.ensure_one()
        self = self.sudo()

        employee_id = self.employee_id
        existed_shifts = employee_id.work_entry_ids.filtered(lambda x: x.state != 'cancelled' and x.date_start and x.date_stop and \
                        ((x.date_start > self.date_from and x.date_start < self.date_to) or (x.date_start <= self.date_from and x.date_stop > self.date_from)))
        
        existed_requests = self.env['hr.shift.change.line'].search([('employee_id', '=', employee_id.id), ('state', '!=', 'cancelled')])\
            .filtered(lambda x: ((x.date_from > self.date_from and x.date_from < self.date_to) or \
            (x.date_from <= self.date_from and x.date_to > self.date_from)))

        status = 'validation'
        if existed_shifts:
            validated_shifts = existed_shifts.filtered(lambda x: x.state == 'validated' and ((x.date_start > self.date_from and x.date_start < self.date_to) or \
                            (x.date_start <= self.date_from and x.date_stop > self.date_from)))
            if validated_shifts:
                status = 'validated-shift'

        if status == 'validation' and existed_requests:
            duplicated_requests = existed_requests.filtered(lambda x: (x.date_from > self.date_from and x.date_to < self.date_to) or \
                                (x.date_from <= self.date_from and x.date_to > self.date_from))
            if duplicated_requests:
                status = 'duplicated-request'
            
        return status

    def name_get(self):
        result = []
        for line in self:
            name = line.order_id.name + ' - [' + str(line.employee_code) + '] ' + line.employee_id.name
            result.append((line.id, name))
        return result
    
    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for line in self:
            period, break_time = 0.0, 0.0
            if line.date_from and line.date_to:
                calendar_id = line.order_id.resource_calendar_id
                intervals = calendar_id._attendance_intervals_batch(line.date_from.replace(tzinfo=UTC), line.date_to.replace(tzinfo=UTC), calendar_id)

                dt = line.date_to - line.date_from
                period =  dt.days * 24 + dt.seconds / 3600 
                break_time = 0.0
                for start, stop, meta in intervals[calendar_id.id]:
                    break_duration = calendar_id._get_breaking_hours(meta, start, stop)
                    if break_duration > 0.0:
                        break_time += break_duration

                if break_time > 0.0:
                    period -= break_time

            line.break_time = break_time
            line.duration = period
