# -*- coding: utf-8 -*-
from odoo import api, fields, models, registry, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AttendanceDeviceUser(models.Model):
    _name = 'attendance.device.user'
    _description = 'Attendance Device User'

    active = fields.Boolean(string='Active', compute='_compute_active', store=True)
    name = fields.Char(string='Name', required=True,
        help='The name of the employee stored in the device')
    device_id = fields.Many2one('attendance.device', string='Attendance Device', required=True, ondelete='cascade')
    uid = fields.Integer(string='UID', readonly=True,
        help='The ID (technical field) of the user/employee in the device storage')
    user_id = fields.Char(string='ID User', size=8, required=True,
        help='The ID Number of the user/employee in the device storage')
    number_id = fields.Char(string='ID Number', size=8, compute='_compute_number_id', store=True, help='The ID Number of the user/employee in the device storage')
    password = fields.Char(string='Password')
    group_id = fields.Integer(string='Group', default=0)
    privilege = fields.Integer(string='Privilege')
    del_user = fields.Boolean(string='Delete User', default=False,
        help='If checked, the user on the device will be deleted upon deleting this record in Odoo')
    employee_id = fields.Many2one('hr.employee', string='Employee', ondelete='set null',
        help='The Employee who is corresponding to this device user')
    hr_attendance_ids = fields.One2many('hr.attendance', 'device_user_id', string='HR Attendances', readonly=True, copy=False)
    hr_attendance_count = fields.Integer(string='HR Attendance Count', compute='_compute_hr_attendance_count', store=True)
    finger_template_ids = fields.One2many('finger.template', 'device_user_id', string='Finger Template', readonly=True)
    finger_template_count = fields.Integer(string='Finger Template Count', compute='_compute_finger_template_count', store=True)
    not_in_device = fields.Boolean(string='Not in Device', readonly=True,
        help="Technical field to indicate this user is not available in device storage. It could be deleted outside Odoo.")

    # _sql_constraints = [
    #     ('employee_id_device_id_unique', 'UNIQUE(employee_id, device_id)', 'The Employee must be unique per Device'),
    # ]

    @api.constrains('user_id', 'device_id')
    def constrains_user_id_device_id(self):
        for record in self:
            if record.device_id and record.device_id.unique_uid:
                if self.search_count([('device_id', '=', record.device_id.id), ('user_id', '=', record.user_id)]) > 1:
                    raise UserError(_('The ID Number must be unique per Device!\nA new user was being created/updated'
                        'whose user_id and device_id is the same as the existing one\'s (name: %s; device: %s; user_id: %s)')
                        % (record.name, record.device_id.display_name, record.user_id))

    def _compute_number_id(self):
        for rec in self:
            rec.number_id = rec.user_id

    @api.depends('hr_attendance_ids')
    def _compute_hr_attendance_count(self):
        for record in self:
            record.hr_attendance_count = len(record.hr_attendance_ids)

    @api.depends('finger_template_ids')
    def _compute_finger_template_count(self):
        for record in self:
            record.finger_template_count = len(record.finger_template_ids)

    @api.depends('device_id', 'employee_id')
    def _compute_active(self):
        for record in self:
            active = record.device_id.active
            if record.employee_id:
                active = record.device_id.active and record.employee_id.active
            record.active = active

    def unlink(self):
        dbname = self._cr.dbname
        for r in self:
            if r.del_user:
                try:
                    cr = registry(dbname).cursor()
                    r = r.with_env(r.env(cr=cr))
                    r.device_id.delete_device_user(r.uid, r.user_id)
                    super(AttendanceDeviceUser, r).unlink()
                except Exception as e:
                    _logger.error(e)
                finally:
                    cr.commit()
                    cr.close()
            else:
                super(AttendanceDeviceUser, r).unlink()
        return True

    def set_device_user(self):
        self.ensure_one()
        new_user = self.device_id.set_device_user(self.uid, self.name, self.privilege, self.password,
            str(self.group_id), str(self.user_id))
        self.upload_finger_templates()
        return new_user

    def upload_finger_templates(self):
        finger_templates = self.mapped('finger_template_ids')
        if not finger_templates:
            if self.employee_id:
                if self.employee_id.finger_template_ids:
                    finger_templates = self.env['finger.template'].create({
                        'device_user_id': self.id,
                        'fid': 0,
                        'valid': self.employee_id.finger_template_ids[0].valid,
                        'template': self.employee_id.finger_template_ids[0].template,
                        'employee_id': self.employee_id.id
                    })
        finger_templates.upload_to_device()

    def action_upload_finger_templates(self):
        for rec in self:
            rec.upload_finger_templates()

    @api.model_create_multi
    def create(self, vals_list):
        users = super(AttendanceDeviceUser, self).create(vals_list)
        if self.env.context.get('should_set_user', False):
            for user in users:
                user.set_device_user()
        return users

    def _prepare_employee_data(self, barcode=None):
        barcode = barcode or self.user_id
        return {
            'name': self.name,
            'created_from_attendance_device': True,
            'barcode': barcode,
            'device_user_ids': [(4, self.id)]
        }

    def generate_employees(self):
        """
        This method will generate new employees from the device user data.
        """
        employees = self.env['hr.employee']

        # prepare employees data
        employee_vals_list = []
        for r in self:
            employee_vals_list.append(r._prepare_employee_data())

        # generate employees
        if employee_vals_list:
            employees = employees.sudo().create(employee_vals_list)

        return employees

    def smart_find_employee(self):
        self.ensure_one()
        employee_id = False
        if self.employee_id:
            employee_id = self.employee_id.id
        else:
            for employee in self.device_id.unmapped_employee_ids:
                if self.user_id == employee.barcode:
                    employee_id = employee.id
        return employee_id

    def action_view_finger_template(self):
        action = self.env.ref('erpvn_attendance_device.action_finger_template')
        result = action.read()[0]

        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        finger_template_count = self.finger_template_count
        if finger_template_count != 1:
            result['domain'] = "[('device_user_id', 'in', " + \
                str(self.ids) + ")]"
        elif finger_template_count == 1:
            res = self.env.ref(
                'erpvn_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_template_ids.id
        return result

    def write(self, vals):
        res = super(AttendanceDeviceUser, self).write(vals)
        if 'name' in vals:
            for r in self:
                r.set_device_user()
        return res