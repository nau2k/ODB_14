# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    department_ids = fields.One2many('resource.department', 'calendar_id', string='Departments')