from odoo import fields, models


class CalendarOverTime(models.Model):
    _inherit ='resource.calendar'

    is_overtime = fields.Boolean(tracking=True)