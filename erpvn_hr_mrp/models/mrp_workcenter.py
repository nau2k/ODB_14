# -*- coding: utf-8 -*-
from datetime import timedelta
from functools import partial
from pytz import timezone

from odoo import api, fields, models, _
from odoo.addons.resource.models.resource import make_aware, Intervals
from odoo.tools.float_utils import float_compare

class MrpWorkcenter(models.Model):
    _name = 'mrp.workcenter'
    _inherit = ['mrp.workcenter', 'mail.thread']

    # add tracking to existed fields.
    code = fields.Char(index=True, tracking=True)
    name = fields.Char(tracking=True)
    time_efficiency = fields.Float(tracking=True)
    resource_calendar_id = fields.Many2one(tracking=True)
    time_start = fields.Float(tracking=True)
    time_stop = fields.Float(tracking=True)
    oee_target = fields.Float(tracking=True)
    capacity = fields.Float(tracking=True)

    department_id = fields.Many2one(string='Department', comodel_name='hr.department', ondelete='restrict', tracking=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees', copy=False,
        compute='_compute_base_department', store=True)
    position_ids = fields.Many2many('hr.job', string='Job Positions', copy=False,
        compute='_compute_base_department', store=True, readonly=False)
    
    employee_work_days = fields.Float(string='Working days/week (E)', compute='_compute_working_hours', store=True)
    employee_work_hours = fields.Float(string='Employee hours/day', compute='_compute_working_hours', store=True)
    employee_work_shift = fields.Integer(string='Shifts/day (E)', compute='_compute_working_hours', store=True)
    
    def action_update_department_in_workcenters(self):
        for rec in self:
            rec._compute_base_department()

    @api.depends('department_id')
    def _compute_base_department(self):
        for workcenter in self:
            workcenter.employee_ids = workcenter.department_id.member_ids
            workcenter.position_ids = workcenter.department_id.jobs_ids

    @api.depends('employee_ids', 'position_ids')
    def _compute_working_hours(self):
        for workcenter in self:
            total_hours_a_day = 0
            for job_id in workcenter.position_ids.filtered(lambda x: x.effective_percent >= 1):
                for e in workcenter.employee_ids.filtered(lambda x: x.job_id.id == job_id.id):
                    total_hours_a_day += (e.resource_calendar_id.hours_per_day * (job_id.effective_percent / 100))
                workcenter.employee_work_days = total_hours_a_day
                workcenter.employee_work_hours = total_hours_a_day
                workcenter.employee_work_shift = total_hours_a_day

    def _get_first_available_slot(self, start_datetime, duration):
        """Override odoo's func to add extra overtime on when planning work order."""
        self.ensure_one()
        start_datetime, revert = make_aware(start_datetime)

        get_available_intervals = partial(self.resource_calendar_id._work_intervals, domain=[('time_type', 'in', ['other', 'leave'])], resource=self.resource_id, tz=timezone(self.resource_calendar_id.tz))
        get_workorder_intervals = partial(self.resource_calendar_id._leave_intervals, domain=[('time_type', '=', 'other')], resource=self.resource_id, tz=timezone(self.resource_calendar_id.tz))

        remaining = duration
        start_interval = start_datetime
        delta = timedelta(days=14)

        for n in range(50):  # 50 * 14 = 700 days in advance (hardcoded)
            dt = start_datetime + delta * n
            available_intervals = get_available_intervals(dt, dt + delta)
            workorder_intervals = get_workorder_intervals(dt, dt + delta)
            for start, stop, dummy in available_intervals:
                # Shouldn't loop more than 2 times because the available_intervals contains the workorder_intervals
                # And remaining == duration can only occur at the first loop and at the interval intersection (cannot happen several time because available_intervals > workorder_intervals
                for i in range(2):
                    interval_minutes = (stop - start).total_seconds() / 60
                    # If the remaining minutes has never decrease update start_interval
                    if remaining == duration:
                        start_interval = start
                    # If there is a overlap between the possible available interval and a others WO
                    if Intervals([(start_interval, start + timedelta(minutes=min(remaining, interval_minutes)), dummy)]) & workorder_intervals:
                        remaining = duration
                    elif float_compare(interval_minutes, remaining, precision_digits=3) >= 0:
                        return revert(start_interval), revert(start + timedelta(minutes=remaining)), 0
                    else:
                        overtime_minutes = self.env.company.limit_overtime_to_plan_workorder * 60.0
                        minute_with_ot = min(remaining, interval_minutes) + overtime_minutes
                        if dummy.day_period == 'afternoon' and not Intervals([(start_interval, start + timedelta(minutes=minute_with_ot), dummy)]) & workorder_intervals \
                            and float_compare(minute_with_ot, remaining, precision_digits=3) >= 0:
                            return revert(start_interval), revert(start + timedelta(minutes=remaining)), abs(remaining - interval_minutes)
                        # Decrease a part of the remaining duration
                        remaining -= interval_minutes
                        # Go to the next available interval because the possible current interval duration has been used
                        break
        return False, 'Not available slot 700 days after the planned start', 0