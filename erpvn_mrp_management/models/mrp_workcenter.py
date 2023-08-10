# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    # add new fields.
    work_days = fields.Float(string='Working days/week', required="True", compute='_compute_work_time')
    work_hours = fields.Float(string='Working hours/shift', required="True", compute='_compute_work_time')
    work_shift = fields.Integer(string='Shifts/day', required="True", compute='_compute_work_time')
    available_capacity = fields.Float(string='Weekly Available', compute='_calculate_wc_capacity', store='True', group_operator='avg')
    hours_uom = fields.Many2one('uom.uom', string='Hours', compute="_get_uom_hours")
    wc_type = fields.Selection([('H', _('Human')),('M', _('Machine')), ('B', _('Both'))], _('Work Center Type'))

    def _get_uom_hours(self):
        uom = self.env.ref('uom.product_uom_hour', raise_if_not_found=False)
        for record in self:
            if uom:
                record.hours_uom = uom.id
        return True


    @api.depends('work_days','work_hours','work_shift','capacity','time_efficiency')
    def _calculate_wc_capacity(self):
        cap = 0.0
        for wc in self:
            cap = wc.work_shift * wc.work_hours * wc.work_days * wc.capacity * wc.time_efficiency / 100
            wc.available_capacity = cap
        return True

    @api.model
    def create(self, vals):
        if not self.code:
            vals['code'] = self.env['ir.sequence'].next_by_code('sequence.workcenter.code')
        return super(MrpWorkcenter, self).create(vals)

    @api.depends('resource_calendar_id')
    def _compute_work_time(self):
        everyday = 0
        for rec in self.resource_calendar_id.attendance_ids:
            temp = (rec.hour_to - rec.hour_from)
            everyday += temp
        #self.work_days = everyday
        self.work_hours = 0
        self.work_shift = 0
        self.work_days = everyday