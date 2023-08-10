
from odoo import api, fields, models, _



class ResignHrEmployee(models.Model):  
    _inherit = 'hr.employee'

    resign_ids = fields.One2many('hr.resignation', 'employee_id', )
