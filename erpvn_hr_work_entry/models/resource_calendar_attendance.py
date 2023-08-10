# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
# import datetime as dt_obj
# from odoo.tools import float_compare
# from odoo.addons.resource.models.resource import string_to_datetime


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    no_fingerprint_required = fields.Boolean(string='No Fingerprint Required', default=False,
        help='If check, the shift is validated with no fingerprint scan required.')
    dayofweek_to = fields.Selection([('0', 'Monday'), ('1', 'Tuesday'), ('2', 'Wednesday'), ('3', 'Thursday'),
        ('4', 'Friday'), ('5', 'Saturday'), ('6', 'Sunday') ], 'Day of Week To', required=True, index=True, default='0')
    break_time_ids = fields.Many2many('hr.break.time', 'break_time_attendance_rel', 'break_id', 'attendance_id', 'Break Time')
    estimated_hours = fields.Float(string='Estimated Hours', compute='_compute_estimated_hours', store=True, readonly=True)

    @api.depends('hour_from', 'hour_to', 'dayofweek', 'dayofweek_to', 'break_time_ids')
    def _compute_estimated_hours(self):
        for record in self:
            if record.dayofweek == record.dayofweek_to:
                record.write({'estimated_hours': record.hour_to - record.hour_from - sum(record.break_time_ids.mapped('duration'))})
            else:
                # 22:00 - 6:00 -> 6.0 - (22.0-24.0)
                estimated_hours = record.hour_to - (record.hour_from - 24.0) - sum(record.break_time_ids.mapped('duration'))

                # add 24.0 hours if overdays.
                day_fr = int(record.dayofweek)
                day_to = int(record.dayofweek_to)
                if day_to < day_fr:
                    day_fr -= 7
                days = day_to - day_fr
                if days > 1:
                    estimated_hours += ((days - 1) * 24.0)
                record.write({'estimated_hours': estimated_hours})

    @api.onchange('hour_from', 'hour_to', 'dayofweek', 'dayofweek_to')
    def _onchange_hours(self):
        if self.dayofweek == self.dayofweek_to:
            super(ResourceCalendarAttendance, self)._onchange_hours()