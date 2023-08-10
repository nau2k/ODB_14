# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MRPWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    def _get_default_worker(self):
        return self.env.user.employee_id

    department_id = fields.Many2one(string='Department', comodel_name='hr.department', 
        ondelete='restrict', readonly=True)
    worker_id = fields.Many2one('hr.employee', string='Worker', 
        default=lambda self: self._get_default_worker())
    employee_code = fields.Char(related='worker_id.barcode', string='Badge ID', store=True)
    
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            workcenter_id = self.env['mrp.workcenter'].browse(val.get('workcenter_id', False))
            val.update({
                'department_id': workcenter_id.department_id.id,
            })
        return super(MRPWorkcenterProductivity, self).create(vals)