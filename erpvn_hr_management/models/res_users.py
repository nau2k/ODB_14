# -*- coding: utf-8 -*-
from odoo import api, fields, models


class User(models.Model):
    _inherit = "res.users"

    allocation_total = fields.Float(related='employee_id.allocation_total')
    allocation_remained = fields.Float(related='employee_id.allocation_remained')
    allocation_taken = fields.Float(related='employee_id.allocation_taken')

    def _get_employee_fields_to_sync(self):
        """
            Không thay đổi name employee khi thay đổi name user.
        """
        res = super(User,self)._get_employee_fields_to_sync()
        if 'name' in res: res.remove('name')
        return res