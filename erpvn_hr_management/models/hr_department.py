# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Department(models.Model):
    _inherit='hr.department'

    sequence = fields.Integer('Sequence', default=10)
    name = fields.Char('Department Name', required=True, translate=True)
    code = fields.Char(string='Code', size=13, required=True)
    mail_channel_id = fields.Many2one(string='Discuss Channel', comodel_name='mail.channel', ondelete='cascade')
    
    @api.model
    def create(self, vals):
        result = super(Department, self).create(vals)
        channel = self.env['mail.channel'].create({
            'public': 'private',
            'channel_type': 'chat',
            'email_send': False,
            'name': vals.get('name'),
            'subscription_department_ids': [(4, result.id)],
        })
        # channel._broadcast(result.parent_id.ids)
        result.write({'mail_channel_id': channel.id})
        return result
    
    def make_channel(self):
        channel = self.env['mail.channel']
        for dept in self:
            channel_id = channel.search([('name', '=', dept.name)])
            if not dept.mail_channel_id:
                if channel_id:
                    dept.write({'mail_channel_id': channel_id.id})
                else:
                    channel_id = channel.create({
                        'public': 'private',
                        'channel_type': 'chat',
                        'email_send': False,
                        'name': dept.name,
                        'subscription_department_ids': [(4, dept.id)],
                    })
                    dept.write({'mail_channel_id': channel_id.id})
            channel_id._broadcast(dept.mapped('member_ids.user_id.partner_id').ids)
            
    def _get_child_departments(self):
        """
        @return: returns a list of id which are all the children of the passed departments and it's id
        """
        children_departments = []
        for dept in self.filtered(lambda d: d.child_ids):
            children_departments += dept.child_ids._get_child_departments()
        return self.mapped('id') + children_departments
    
    def _get_parent_departments(self):
        """
        @return: returns a list of id which are all level of the parent of the passed departments and it's id
        """
        parent_departments = []
        if self.parent_id:
            parent_departments += self.parent_id._get_parent_departments()
        return self.mapped('id') + parent_departments