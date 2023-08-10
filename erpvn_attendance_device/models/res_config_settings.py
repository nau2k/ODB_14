# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    limited_hours_to_get_attendances = fields.Integer(
        related='company_id.limited_hours_to_get_attendances', readonly=False,
        string='Limited Hours To Get Attendances Automatically (Hours)')

    attendance_range_in_minutes = fields.Integer(
        related='company_id.attendance_range_in_minutes', readonly=False,
        string='The Limited Range Between Check In And Out (Minutes)')
    
    limited_hours_between_in_out = fields.Integer(
        related='company_id.limited_hours_between_in_out', readonly=False,
        string='Limited Hours Between Check In And Check Out (Hours)')