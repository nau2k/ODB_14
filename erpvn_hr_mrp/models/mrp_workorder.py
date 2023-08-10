# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    department_id = fields.Many2one(string=_('Department'), comodel_name='hr.department')
    duration_overtime = fields.Float(
        'Overtime Duration', digits=(16, 2), default=0.0,
        states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
        help="Overtime duration (in minutes)")
    
    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            val.update({'department_id': self.env['mrp.workcenter'].browse(val.get('workcenter_id', False)).department_id.id})
        return super(MrpWorkorder, self).create(vals)

    def action_update_department(self):
        for record in self:
            record.department_id = record.workcenter_id.department_id

    def _set_dates_planned(self):
        if not self[0].date_planned_start or not self[0].date_planned_finished:
            if not self.leave_id:
                return
            raise UserError(_("It is not possible to unplan one single Work Order. "
                              "You should unplan the Manufacturing Order instead in order to unplan all the linked operations."))
        date_from = self[0].date_planned_start
        date_to = self[0].date_planned_finished
        to_write = self.env['mrp.workorder']
        for wo in self.sudo():
            if wo.leave_id:
                to_write |= wo
            else:
                wo.leave_id = wo.env['resource.calendar.leaves'].create({
                    'name': wo.display_name,
                    'calendar_id': wo.workcenter_id.resource_calendar_id.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'resource_id': wo.workcenter_id.resource_id.id,
                    'workorder_id': wo.id,
                    'production_id': wo.production_id.id,
                    'time_type': 'other',
                })
        to_write.leave_id.write({
            'date_from': date_from,
            'date_to': date_to,
        })
