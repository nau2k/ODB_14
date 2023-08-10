# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'
    
    @api.depends('date_from', 'date_to')
    def _compute_duration(self):
        for leave in self:
            res = 0.0
            if leave.date_from and leave.date_to and leave.calendar_id:
                breaking_hours = 0.0
                attendance_ids = leave.calendar_id.attendance_ids.filtered(lambda x: x.dayofweek == str(leave.date_from.date().weekday()))
                
                if attendance_ids:
                    start_time_tz = self.env['erpvn.base'].convert_utc_time_to_tz(leave.date_from, leave.resource_id.tz)
                    stop_time_tz = self.env['erpvn.base'].convert_utc_time_to_tz(leave.date_to, leave.resource_id.tz)
                    breaking_hours = sum(leave.calendar_id._get_breaking_hours(att, start_time_tz, stop_time_tz) for att in attendance_ids)

                res = ((leave.date_to - leave.date_from).total_seconds() / 3600) - breaking_hours
                
            leave.duration = res