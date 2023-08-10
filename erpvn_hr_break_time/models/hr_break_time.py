# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from pytz import timezone, UTC


class HRBreakTime(models.Model):
    _name = 'hr.break.time'
    _description = 'Breaking Hours'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(default=10, help="Gives the sequence of this line when displaying the resource calendar.")
    name = fields.Char(string='Name', required=True, translate=True,
        help='The name of the attendance activity. E.g. Normal Working, Overtime, etc')
    hour_from = fields.Float(string='Work from', required=True, index=True,
        help="Start and End time of working. A specific value of 24:00 is interpreted as 23:59:59.999999.")
    hour_to = fields.Float(string='Work to', required=True)
    duration = fields.Float(compute='_compute_duration', store=True, string="Period")
    break_line_ids = fields.One2many('hr.break.time.line', 'break_id', string='Breaking Line')
    description = fields.Text(string='Description',)
    

    @api.onchange('hour_from', 'hour_to')
    def _onchange_hours(self):
        # avoid negative or after midnight
        self.hour_from = min(self.hour_from, 23.99)
        self.hour_from = max(self.hour_from, 0.0)
        self.hour_to = min(self.hour_to, 23.99)
        self.hour_to = max(self.hour_to, 0.0)
        # # avoid wrong order
        self.hour_to = max(self.hour_to, self.hour_from)

    @api.depends('hour_from', 'hour_to')
    def _compute_duration(self):
        for record in self:
            record.duration = record._get_duration(record.hour_from, record.hour_to)

    def _get_duration(self, hour_from, hour_to):
        if not hour_from or not hour_to:
            return 0
        return hour_to - hour_from

    def _check_input_datetime(self, start_dt, end_dt):
        if start_dt > end_dt:
            raise ValidationError(_('Datetime range is not valid.'))
        elif start_dt.tzinfo and end_dt.tzinfo:
            if start_dt.tzinfo != end_dt.tzinfo:
                raise ValidationError(_('Timezone of datetime range is not valid.'))
            elif start_dt.tzinfo != UTC:
                # incase input timezone different than UTC.
                INPUT_TZ = start_dt.tzinfo
                start_dt = INPUT_TZ.localize(start_dt.replace(tzinfo=None)).astimezone(UTC).replace(tzinfo=None)
                end_dt = INPUT_TZ.localize(end_dt.replace(tzinfo=None)).astimezone(UTC).replace(tzinfo=None)

        return start_dt, end_dt

    def _get_float_hours(self, start_dt, end_dt):
        USER_TZ = timezone(self.env.user.tz)
        # convert utc tz to user's tz.
        start_dt = UTC.localize(start_dt).astimezone(USER_TZ).replace(tzinfo=None)
        end_dt = UTC.localize(end_dt).astimezone(USER_TZ).replace(tzinfo=None)
        # convert dt to
        start_float = start_dt.time().hour + start_dt.time().minute/60
        end_float = end_dt.time().hour + end_dt.time().minute/60

        return start_float, end_float

    def has_breaking_hours(self, start_dt, end_dt, domain=None):
        start_dt, end_dt = self._check_input_datetime(start_dt, end_dt)
        if start_dt == end_dt:
            return False

        # domain = [('department_id', '=', department_id.id)]
        domain = domain if domain is not None else []
        breaking_lines = self.env['hr.break.time.line'].search(domain)
        # datetime range over a days.
        if (end_dt - start_dt).days > 0:
            if breaking_lines.mapped('break_id').filtered(lambda x: x.duration > 0):
                return True

        start_float, end_float = self._get_float_hours(start_dt, end_dt)
        result = False
        for break_id in breaking_lines.mapped('break_id'):
            if start_float <= break_id.hour_from and end_float >= break_id.hour_to and break_id.duration > 0:
                result = True
            elif start_float > break_id.hour_from and end_float >= break_id.hour_to and (break_id.hour_to - start_float) > 0:
                result = True
            elif start_float <= break_id.hour_from and end_float < break_id.hour_to and (end_float - break_id.hour_from) > 0:
                result = True
                
            if result:
                break

        return result

    def get_breaking_hours(self, start_dt, end_dt, domain=None):
        start_dt, end_dt = self._check_input_datetime(start_dt, end_dt)
        if start_dt == end_dt:
            return 0.0

        # domain = [('department_id', '=', department_id.id)]
        domain = domain if domain is not None else []
        breaking_lines = self.env['hr.break.time.line'].search(domain)
        # datetime range over a days.
        if (end_dt - start_dt).days > 0:
            return sum(breaking_lines.break_id.mapped('duration'))

        start_float, end_float = self._get_float_hours(start_dt, end_dt)
        result = 0.0
        for break_id in breaking_lines.mapped('break_id'):
            if start_float <= break_id.hour_from and end_float >= break_id.hour_to:
                result += break_id.duration
            elif start_float > break_id.hour_from and end_float >= break_id.hour_to:
                result += (break_id.hour_to - start_float) if (break_id.hour_to - start_float) > 0 else 0
            elif start_float <= break_id.hour_from and end_float < break_id.hour_to:
                result += (end_float - break_id.hour_from) if (end_float - break_id.hour_from) > 0 else 0
            
        return result