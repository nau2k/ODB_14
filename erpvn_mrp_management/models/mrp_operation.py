from odoo import models, fields, api, tools

class MrpOperation(models.Model):
    _name = 'mrp.operation'
    _description = 'MRP Operation'


    name = fields.Char('Operation', translate=True)
    sequence = fields.Integer('Sequence', default=10)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', check_company = True)
    department_name = fields.Char(string='Department', related='workcenter_id.name', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', default = lambda self: self.env.company)