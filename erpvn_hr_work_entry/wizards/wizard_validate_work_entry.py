# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime, time, timedelta
from odoo import fields, models, api, _
from odoo.addons.erpvn_hr_work_entry.models.hr_work_entry import HOLIDAY_CODES


class WizardValidateWorkEntry(models.TransientModel):
    _name = "wizard.validate.work.entry"
    _description = "Wizard Validate Work Entry"

    name = fields.Char()
    department_ids = fields.Many2many('hr.department', string='Departments')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    date_from = fields.Date(string='From', default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_to = fields.Date(string='To', default=lambda self: fields.Date.context_today(self) + relativedelta(months=+1, day=1, days=-1))
    action_type = fields.Selection(string='Action Type', selection=[('0', 'none'), ('1', 'confirm'), ('2', 'validate'), ('3', 'draft')], default='0')
    
    def _get_domain(self):
        self.ensure_one()
        domain=[]
        base_obj = self.env['erpvn.base']

        if self.date_from:
            datetime_from_user_tz = datetime.combine(self.date_from, time.min)
            datetime_from_utc = base_obj.convert_time_to_utc(datetime_from_user_tz).replace(tzinfo=None)
            domain += [('date_start', '>=', datetime_from_utc)]
        if self.date_to:
            datetime_to_user_tz = datetime.combine(self.date_to, time.max)
            datetime_to_utc = base_obj.convert_time_to_utc(datetime_to_user_tz).replace(tzinfo=None)
            domain += [('date_stop', '<=', datetime_to_utc)]
        if self.employee_ids:
            domain += [('employee_id', 'in', self.employee_ids.ids)]
        if self.department_ids:
            domain += [('department_id', 'in', self.department_ids.ids)]

        return domain

    def action_set_to_draft(self):
        self.ensure_one()
        domain=self._get_domain()
        return self.env['hr.work.entry'].search(domain).action_set_to_draft()

    def action_confirm(self):
        self.ensure_one()
        domain=self._get_domain()
        return self.env['hr.work.entry'].search(domain).action_confirm()

    def action_validate(self):
        self.ensure_one()
        domain = self._get_domain() + [('hr_attendance_ids', '!=', False)]
        return self.env['hr.work.entry'].search(domain).action_validate()

    def action_batch_fix_attendance(self):
        self.ensure_one()
        domain = self._get_domain() + [('hr_attendance_ids', '!=', False)]
        return self.env['hr.work.entry'].search(domain).action_fix_attendance()

    def action_batch_create_work_entry(self):
        self.ensure_one()

        contract_domain=[]
        if self.department_ids:
            contract_domain = [('employee_id', 'in', self.department_ids.member_ids.ids)]
        if self.employee_ids:
            contract_domain = [('employee_id', 'in', self.employee_ids.ids)]

        contract_domain += [
            ('state', 'in', ('open', 'close', 'expiring')),
            '|', ('date_end', '=', False), ('date_end', '>', self.date_from)
        ]

        work_entry_obj = self.env['hr.work.entry']
        work_entry_vals = []
        dt_from = self.date_from + relativedelta(hour=0, minute=0, second=0)
        dt_to = self.date_to + relativedelta(hour=23, minute=59, second=59)

        for contract_id in self.env['hr.contract'].sudo().search(contract_domain):
            current_date = dt_from
            days_of_week = list(set(contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek')))

            while current_date <= dt_to:
                if contract_id.date_end:
                    if contract_id.date_end < current_date.date():
                        break
                if str(current_date.weekday()) in days_of_week:
                    for attendence_id in contract_id.resource_calendar_id.attendance_ids.filtered(lambda x: x.dayofweek == str(current_date.weekday())):
                        utc_tz_dt_start, utc_tz_dt_stop = work_entry_obj._get_utc_tz(attendence_id, current_date)

                        if contract_id.employee_id.work_entry_ids.filtered_domain([
                            ('attendance_id', '=', attendence_id.id),
                            ('date_start', '=', utc_tz_dt_start),
                            ('date_stop', '=', utc_tz_dt_stop)
                        ]):
                            continue

                        if contract_id.employee_id.work_entry_ids.filtered(lambda x: x.date_start and x.date_stop)\
                            .filtered(lambda y: y.date_start <= utc_tz_dt_stop and y.date_stop >= utc_tz_dt_start):
                            continue

                        if self.env['hr.leave'].sudo().search_count([
                            ('state', '=', 'validate'),
                            ('date_from', '<=', utc_tz_dt_start),
                            ('date_to', '>=', utc_tz_dt_stop),
                            ('employee_id', '=', contract_id.employee_id.id),
                            ('holiday_status_id.code', 'in', HOLIDAY_CODES)]) > 0:
                            continue

                        val = work_entry_obj._prepare_work_entry_vals(contract_id, attendence_id, current_date, utc_tz_dt_start, utc_tz_dt_stop)

                        if self.env['hr.leave'].sudo().search_count([
                            ('state', '=', 'validate'),
                            ('date_from', '<=', utc_tz_dt_start),
                            ('date_to', '>=', utc_tz_dt_stop),
                            ('employee_id', '=', contract_id.employee_id.id)]) > 0:
                            val.update({
                                'state': 'validated',
                                'actual_start': utc_tz_dt_start,
                                'actual_stop': utc_tz_dt_stop,
                            })

                        if val not in work_entry_vals:
                            work_entry_vals.append(val)
                            
                current_date += timedelta(days=1)
            
        if work_entry_vals:
            work_entry_obj.create(work_entry_vals)