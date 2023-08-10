# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class UpdateAttendanceWizard(models.TransientModel):
    _inherit = 'attendance.update.wizard'

    def _get_valid_working_shifts(self):
        res = super()._get_valid_working_shifts()
        return res.filtered(lambda x: not x.is_overtime)