# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
# from odoo.exceptions import UserError
# from odoo.addons.base.models.res_partner import _tz_get
# from odoo.addons.resource.models.resource import float_to_time
# from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
# from datetimerange import DateTimeRange
# from collections import defaultdict



class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    def _get_leave_requests(self, date_from, date_to):
        leave_obj = self.env['hr.leave']
        base_obj = self.env['erpvn.base']

        dt_from = datetime.combine(date_from, datetime.min.time())
        dt_from = base_obj.convert_time_to_utc(dt=dt_from).replace(tzinfo=None)
        dt_to = datetime.combine(date_to, datetime.max.time())
        dt_to = base_obj.convert_time_to_utc(dt=dt_to).replace(tzinfo=None)

        leave_domain = [
            ('employee_id', '=', self.employee_id.id),
            '|', '|',
            '&', '&', ('date_from', '>=', dt_from), ('date_to', '>', dt_to), ('date_from', '<', dt_to),
            '&', '&', ('date_to', '>', dt_from), ('date_from', '<', dt_from), ('date_to', '<=', dt_to),
            '&', ('date_to', '<=', dt_to), ('date_from', '>=', dt_from)
        ]
            
        return leave_obj.search(leave_domain)

    def _update_from_holidays(self):
        self.ensure_one()
        
        validated_leaves = self._get_leave_requests(self.date_start, self.date_stop).filtered(lambda x: x.state == 'validate' and \
                           (x.number_of_days > 0.0 or x.number_of_hours_display > 0.0))

        if validated_leaves:
            for l in validated_leaves:
                if self.date_start <= l.date_to and self.date_stop >= l.date_from \
                        and not self.date_start == l.date_to and not self.date_stop == l.date_from: # exclude continues time ranges.

                    if self.actual_start >= l.date_from and self.actual_stop <= l.date_to:
                        w_note = (self.note or '') + _('\nUpdate actual by time off "%s: %s"') % \
                            (str(l.holiday_status_id.name), str(l.name))
                        self.sudo().write({
                            'actual_start': self.date_start,
                            'actual_stop': self.date_start,
                            'note': w_note,
                        })
                    elif self.actual_start < l.date_from and self.actual_stop <= l.date_to:
                        w_note = (self.note or '') + _('\nUpdate actual to by time off "%s: %s"') % \
                            (str(l.holiday_status_id.name), str(l.name))
                        self.sudo().write({
                            'actual_stop': l.date_from,
                            'note': w_note,
                        })

                    elif self.actual_start >= l.date_from and self.actual_stop > l.date_to:
                        w_note = (self.note or '') + _('\nUpdate actual from by time off "%s: %s"') % \
                            (str(l.holiday_status_id.name), str(l.name))
                        self.sudo().write({
                            'actual_start': l.date_to,
                            'note': w_note,
                        })

    def action_confirm(self):
        work_entries = self.filtered(lambda x: x.state == 'draft')

        res = super().action_confirm()

        for w in work_entries.filtered(lambda x: x.state == 'confirmed'):
            w._update_from_holidays()

        return res