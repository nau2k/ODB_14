# -*- coding: utf-8 -*-
from . import models
from . import wizard

from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    attendances_to_update = env['hr.attendance'].search([('state', '=', 'draft'), ('no_check_in', '=', True)])
    attendances_to_update.write({'state': 'no_check_in'})