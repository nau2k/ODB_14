# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    workcenter_id = fields.Many2one(string='WorkCenter', comodel_name='mrp.workcenter')

    def get_related_fields(self):
        # Khi resource_type thay đổi, thì kiểm tra và cập nhật các field ở trên
        for obj in self:
            vals = {}
            if obj.resource_type == 'user':
                emp_obj = self.env['hr.employee'].search([('resource_id', '=', obj.id)])
                vals.update({
                    'employee_id': emp_obj.id,
                    'department_id': emp_obj.department_id.id,
                })
            elif obj.resource_type == 'material':
                wcenter_obj = self.env['mrp.workcenter'].search([('resource_id', '=', obj.id)])
                vals.update({
                    'workcenter_id': wcenter_obj.id,
                    'department_id': wcenter_obj.department_id.id,
                })
            obj.write(vals)
