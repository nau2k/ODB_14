# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class Department(models.Model):
    _inherit = "hr.department"

    def write(self, vals):
        if 'manager_id' in vals:
            self.env.context = dict(self.env.context)
            self.env.context.update({'update_department_manager': True})
        return super(Department, self).write(vals)