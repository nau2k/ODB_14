# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AttendanceState(models.Model):
    _name = 'attendance.state'
    _description = 'Attendance State'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, translate=True, tracking=True,
        help='The name of the attendance state. E.g. Login, Logout, Overtime Start, etc')
    code = fields.Integer(string='Code Number', required=True, tracking=True,
        help='An integer to express the state code')
    type = fields.Selection([('check_in', 'Check-in'), ('check_out', 'Check-out')], string='Activity Type', required=True, tracking=True)
    work_entry_type_id = fields.Many2one('hr.work.entry.type', string='Entry Type', tracking=True,
        help='Attendance activity, e.g. Normal Working, Overtime, etc')
    
    def name_get(self):
        """name_get that supports displaying tags with their code as prefix"""
        result = []
        for record in self:
            if record.work_entry_type_id:
                result.append((record.id, '[' + record.work_entry_type_id.name + '] ' + record.name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """name search that supports searching by tag code"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('work_entry_type_id.name', '=ilike', name + '%'), ('name', operator, name)]
        state = self.search(domain + args, limit=limit)
        return state.name_get()