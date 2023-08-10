# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.tools.float_utils import float_round

class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    mode_id = fields.Many2one(string='Mode Type', comodel_name='hr.leave.mode.type', ondelete='restrict',)
    request_unit = fields.Selection(default='day')
    description = fields.Html(string='Description',)

    def get_employees_days(self, employee_ids):
        self = self.sudo()
        return super(HolidaysType, self).get_employees_days(employee_ids)

    def name_get(self):
        if not self._context.get('employee_id'):
            return super(HolidaysType, self).name_get()
        res = []
        for record in self:
            name = record.name
            if record.allocation_type != 'no':
                remain = record.virtual_remaining_leaves or 0.0
                total = record.max_leaves or 0.0

                if record.request_unit == 'hour':
                    name = "%(name)s (%(count)s)" % {
                        'name': record.name,
                        'count': _('%s:%s remaining out of %s:%s') % (
                            int(remain), round((remain % 1) * 60),
                            int(total), round((total % 1) * 60),
                        ) + _(' hours')
                    }
                else:
                    name = "%(name)s (%(count)s)" % {
                        'name': name,
                        'count': _('%g remaining out of %g') % (
                            float_round(remain, precision_digits=2) or 0.0,
                            float_round(total, precision_digits=2) or 0.0,
                        ) + _(' days')
                    }
            res.append((record.id, name))
        return res