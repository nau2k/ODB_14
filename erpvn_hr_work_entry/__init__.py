# -*- coding: utf-8 -*-
from . import models
from . import wizards
from . import reports
from . import controllers

from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for attedance in env['resource.calendar.attendance'].search([]):
        dayofweek_to = attedance.dayofweek
        if attedance.hour_to < attedance.hour_from:
            dayofweek_to_number = int(dayofweek_to) + 1
            if dayofweek_to_number > 6:
                dayofweek_to_number = 0
            dayofweek_to = str(dayofweek_to_number)
        vals = {'dayofweek_to': dayofweek_to}
        if not attedance.work_entry_type_id and attedance._default_work_entry_type_id():
            vals.update({'work_entry_type_id': attedance._default_work_entry_type_id()[0].id})
        attedance.write(vals)