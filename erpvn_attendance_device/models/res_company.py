# -*- encoding: utf-8 -*-
from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = "res.company"

    limited_hours_to_get_attendances = fields.Integer(store=True, readonly=False,
        default=4, string='Limited Hours To Get Attendances Automatically (Hours)')
    attendance_range_in_minutes = fields.Integer(store=True, readonly=False, 
        default=5, string='The Limited Range Between Check In And Out (Minutes)')
    limited_hours_between_in_out = fields.Integer(store=True, readonly=False,
        default=13, string='Limited Hours Between Check In And Check Out (Hours)')