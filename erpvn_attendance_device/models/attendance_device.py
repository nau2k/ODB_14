# -*- coding: utf-8 -*-
import pytz, logging, time
from datetime import datetime, timedelta
from datetimerange import DateTimeRange
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, registry, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.addons.erpvn_base.models.base import OdooBase

from ..pyzk.zk import ZK
from ..pyzk.zk.user import User
from ..pyzk.zk.exception import ZKErrorResponse, ZKNetworkError, ZKConnectionUnauthorized

_logger = logging.getLogger(__name__)


class AttendanceDevice(models.Model):
    _name = 'attendance.device'
    _description = 'Attendance Device'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'erpvn.base']

    def _get_default_attendance_states(self):
        att_state_ids = self.env['attendance.state']

        # Normal Working Attendance
        attendance_device_state_in_code_0 = self.env.ref('erpvn_attendance_device.attendance_device_state_in_code_0', False)
        if attendance_device_state_in_code_0:
            att_state_ids |= attendance_device_state_in_code_0
        attendance_device_state_out_code_1 = self.env.ref('erpvn_attendance_device.attendance_device_state_out_code_1', False)
        if attendance_device_state_out_code_1:
            att_state_ids |= attendance_device_state_out_code_1
        # Overtime Working Attendance
        attendance_device_state_in_code_4 = self.env.ref('erpvn_attendance_device.attendance_device_state_in_code_4', False)
        if attendance_device_state_in_code_4:
            att_state_ids |= attendance_device_state_in_code_4
        attendance_device_state_out_code_5 = self.env.ref('erpvn_attendance_device.attendance_device_state_out_code_5', False)
        if attendance_device_state_out_code_5:
            att_state_ids |= attendance_device_state_out_code_5
        return att_state_ids

    @api.model
    def _get_default_attendance_device_state_lines(self):
        attendance_device_state_line_data = []
        for state in self._get_default_attendance_states():
            attendance_device_state_line_data.append(
                (0, 0, {
                    'attendance_state_id': state.id,
                    'code': state.code,
                    'type': state.type,
                    'work_entry_type_id': state.work_entry_type_id.id
                })
            )
        return attendance_device_state_line_data

    def _get_user_group(self):
        group_id = self.env['ir.model.data'].xmlid_to_res_id(
            'erpvn_planning_management.planning_mrp_user')
        user_ids = OdooBase.get_users_from_group(self, group_id)
        return [('id', 'in', user_ids)]

    active = fields.Boolean(string='Active', default=True, tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], string='Status',
        default='draft', index=True, copy=False, required=True, tracking=True)
    name = fields.Char(string="Name", required=True, help='The name of the attendance device', tracking=True, translate=True,
        copy=True, default='/', readonly=True, states={'draft': [('readonly', False)]})
    firmware_version = fields.Char(string='Firmware Version', readonly=True,
        help="The firmware version of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    serialnumber = fields.Char(string='Serial Number', readonly=True,
        help="The serial number of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    oem_vendor = fields.Char(string='OEM Vendor', readonly=True, 
        help="The OEM Vendor of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    platform = fields.Char(string='Platform', readonly=True,
        help="The Platform of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    device_name = fields.Char(string='Device Name', readonly=True,
        help="The model of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    work_code = fields.Char(string='Work Code', readonly=True,
        help="The Work Code of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    face_version = fields.Char(string='Face Version', readonly=True,
                              help="The Face Version of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    fingerprint_version = fields.Char(string='Fingerprint Version', readonly=True,
                              help="The ingerprint Version of the device which will be filled automatically when you hit the 'Get Device Info' button.")
    ip = fields.Char(string="IP / Domain Name", required=True, tracking=True, copy=False, readonly=True, states={'draft': [('readonly', False)]},
        help='The accessible IP or Domain Name of the device to get device\'s attendance data', default='0.0.0.0')
    port = fields.Integer(string="Port", required=True, default=4370, tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    punch_type_by = fields.Selection([
        ('system', 'System'),
        ('device', 'Device'),], string='Punch State By', default='device', required=True, tracking=True)
    timeout = fields.Integer(string='Timeout', default=20, required=True, help='Connection Timeout in second', tracking=True,
        readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text(string="Description")
    user_id = fields.Many2one('res.users', string="Technician", tracking=True, default=lambda self: self.env.user, domain=_get_user_group)
    device_user_ids = fields.One2many('attendance.device.user', 'device_id', string='Device Users',
        help='List of Users stored in the attendance device')
    device_users_count = fields.Integer(string='Users Count', compute='_compute_device_users_count', store=True)
    mapped_employee_ids = fields.Many2many('hr.employee', 'mapped_device_employee_rel', string='Mapped Employees',
        compute='_compute_employees', store=True, help="List of employees that have been mapped with this device's users")
    mapped_employees_count = fields.Integer(string='Mapped Employee Count', compute='_compute_mapped_employees_count', store=True)
    umapped_device_user_ids = fields.One2many('attendance.device.user', 'device_id', string='Unmapped Device Users', domain=[('employee_id', '=', False)],
        help='List of Device Users that have not been mapped with an employee')
    unmapped_employee_ids = fields.Many2many('hr.employee', 'device_employee_rel', 'device_id', 'employee_id',
        compute='_compute_employees', store=True, string='Unmapped Employees', help="The employees that have not been mapped with any user of this device")
    attendance_device_state_line_ids = fields.One2many('attendance.device.state.line', 'device_id', string='State Codes', copy=False,
        default=_get_default_attendance_device_state_lines, readonly=True, states={'draft': [('readonly', False)]})
    location_id = fields.Many2one('attendance.device.location', string='Location', tracking=True, required=True,
        help='The location where the device is located', readonly=True, states={'draft': [('readonly', False)]})
    ignore_unknown_code = fields.Boolean(string='Ignore Unknown Code', default=False, tracking=True, readonly=True, states={'draft': [('readonly', False)]},
        help='Sometimes you don\'t want to load attendance data with status codes those not declared in the table below. In such the case, check this field.')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True, states={'draft': [('readonly', False)]})
    auto_clear_attendance = fields.Boolean(string='Auto Clear Attendance Data', default=False, tracking=True, readonly=True, states={'draft': [('readonly', False)]},
        help='Check this to clear all device attendance data after download into Odoo')
    auto_clear_attendance_schedule = fields.Selection([('on_download_complete', 'On Download Completion'), ('time_scheduled', 'Time Scheduled')],
        string='Auto Clear Schedule', required=True, default='on_download_complete', tracking=True,
        help="On Download Completion: Delete attendance data as soon as download finished\nTime Scheduled: Delete attendance data on the time specified below")
    auto_clear_attendance_hour = fields.Float(string='Auto Clear At', tracking=True, required=True, default=0.0,
        help="The time (in the attendance device's timezone) to clear attendance data after download.")
    auto_clear_attendance_dow = fields.Selection([
        ('-1', 'Everyday'),
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday')], string='Auto Clear On', default='-1', required=True, tracking=True)
    auto_clear_attendance_error_notif = fields.Boolean(string='Auto Clear Attendance Notif.', default=True, tracking=True,
        help='Notify upon no safe found to clear attendance data')
    tz = fields.Selection('_tz_get', string='Time zone', compute='_compute_tz', store=True,
        help="The device's timezone, used to output proper date and time values inside attendance reports.")
    unique_uid = fields.Boolean(string='Unique UID', default=True, required=True, tracking=True, readonly=True, states={'draft': [('readonly', False)]},
        help='Some Bad Devices allow uid duplication. In this case, uncheck this field. But it is recommended to change your device.')
    last_attendance_download = fields.Datetime(string='Last Sync.', readonly=True, help='The last time that the attendance data was downlowed from the device into Odoo.')
    map_before_dl = fields.Boolean(string='Map Employee Before Download', default=True,
        help='Always try to map users and employees (if any new found) before downloading attendance data.')
    create_employee_during_mapping = fields.Boolean(string='Generate Employees During Mapping', default=False,
        help="If checked, during mapping between Device's Users and company's employees, umapped device users will try to create a new employee then map accordingly.")
    download_error_notification = fields.Boolean(string='Download Error Notification', default=True, readonly=True, states={'draft': [('readonly', False)]},
        help='Enable this to get notified when data download error occurs.')
    debug_message = fields.Boolean(string='Debug Message', default=False, help="If checked, debugging messages will be posted in OpenChatter for debugging purpose")
    total_att_records = fields.Integer(string='Attendance Records', compute='_compute_total_attendance_records')
    finger_template_ids = fields.One2many('finger.template', 'device_id', string='Finger Template', readonly=True)
    finger_template_count = fields.Integer(string='Finger Templates', compute='_compute_finger_template_count', store=True)
    protocol = fields.Selection([('udp', 'UDP'), ('tcp', 'TCP')], string='Protocol', required=True, default='tcp', tracking=True,
        help="Some old devices do not support TCP. In such the case, please try on switching to UDP.")
    omit_ping = fields.Boolean(string='Omit Ping', default=True, readonly=True, states={'draft': [('readonly', False)]}, help='Omit ping ip address when connecting to device.')
    password = fields.Char(string='Password', readonly=True, states={'draft': [('readonly', False)]}, help="The password to authenticate the device, if required")
    unaccent_user_name = fields.Boolean(string='Unaccent User Name', default=True, tracking=True,
        help="Some Devices support Unicode names such as the ZKTeco K50, some others do not. In addition to this, the name field on devices is usually "
        "limited at about 24 Latin characters or less Unicode characters. Unaccent is sometimes a workaround for long Unicode names")

    zk = None
    zk_cache = {}

    _sql_constraints = [
        ('ip_and_port_unique', 'UNIQUE(ip, port, location_id)', 'You cannot have more than one device with the same ip and port of the same location!'),
    ]

    def _set_zk(self):
        """
        This method return a ZK object.
        If an object corresponding to the connection param was created
        and available in self.zk_cache, it will be return. To avoid it, call it with .with_context(no_zk_cache=True)        
        """
        self.ensure_one()
        force_udp = self.protocol == 'udp'
        password = self.password or 0
        cached_key = self.protocol + \
            str(self.omit_ping) + str(self.timeout) + str(password)
        if self.ip:
            cached_key += self.ip
        if self.port:
            cached_key += str(self.port)

        if not cached_key in self.zk_cache.keys() or self.env.context.get('no_zk_cache', False):
            self.zk_cache[cached_key] = ZK(
                self.ip, self.port, self.timeout, password=password, force_udp=force_udp, ommit_ping=self.omit_ping)

        # self.zk = self.zk_cache[cached_key]
        self.__class__.zk = self.zk_cache[cached_key]

    @api.model
    def _tz_get(self):
        return [(x, x) for x in pytz.all_timezones]

    @api.depends('location_id.tz')
    def _compute_tz(self):
        default_tz = self.env.context.get('tz') or self.env.user.tz
        for r in self:
            if r.location_id and r.location_id.tz:
                default_tz = r.location_id.tz
            r.tz = default_tz

    def name_get(self):
        """name_get that supports displaying location name and model as prefix"""
        result = []
        for r in self:
            name = r.name
            if r.oem_vendor:
                if r.device_name:
                    name = "[%s %s] %s" % (name, r.oem_vendor, r.device_name)
                else:
                    name = "[%s] %s" % (name, r.oem_vendor)
            if r.location_id:
                name = "[%s] %s" % (r.location_id.name, name)
            result.append((r.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """name search that supports searching by tag code"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('location_id.name', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&'] + domain
        state = self.search(domain + args, limit=limit)
        return state.name_get()

    @api.depends('device_user_ids')
    def _compute_device_users_count(self):
        total_att_data = self.env['attendance.device.user'].read_group([('device_id', 'in', self.ids)], ['device_id'], ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.device_users_count = mapped_data.get(r.id, 0)

    @api.depends('finger_template_ids')
    def _compute_finger_template_count(self):
        total_att_data = self.env['finger.template'].read_group([('device_id', 'in', self.ids)], ['device_id'], ['device_id'])
        mapped_data = dict([(dict_data['device_id'][0], dict_data['device_id_count']) for dict_data in total_att_data])
        for r in self:
            r.finger_template_count = mapped_data.get(r.id, 0)

    def _compute_total_attendance_records(self):
        for rec in self:
            rec.total_att_records = self.env['hr.attendance'].search_count(['|', ('device_in_id', '=', rec.id), ('device_out_id', '=', rec.id)])

    @api.depends('device_user_ids', 'device_user_ids.active', 'device_user_ids.employee_id', 'device_user_ids.employee_id.active')
    def _compute_employees(self):
        HrEmployee = self.env['hr.employee']
        for r in self:
            r.update({
                'unmapped_employee_ids': [(6, 0, HrEmployee.search([('id', 'not in', r.device_user_ids.mapped('employee_id').ids)]).ids)],
                'mapped_employee_ids': [(6, 0, r.device_user_ids.mapped('employee_id').filtered(lambda employee: employee.active == True).ids)],
            })

    @api.depends('mapped_employee_ids')
    def _compute_mapped_employees_count(self):
        for r in self:
            r.mapped_employees_count = len(r.mapped_employee_ids)

    @api.onchange('unique_uid')
    def onchange_unique_uid(self):
        if not self.unique_uid:
            message = _('This is for experiment to check if the device contains bad data with non-unique user\'s uid. '
                'Turn this option off will allow mapping device user\'s user_id with user\'s user_id in Odoo.\n'
                'NOTE:\n- non-latin user_id are not supportted.\n- Do not turn this option off in production.')
            return {
                'warning': {
                    'title': "Warning!",
                    'message': message,
                },
            }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'ip' in vals:
                vals['ip'] = vals['ip'].strip()
        return super(AttendanceDevice, self).create(vals_list)

    def write(self, vals):
        if 'ip' in vals:
            vals['ip'] = vals['ip'].strip()
        return super(AttendanceDevice, self).write(vals)

    def connect(self):
        self.ensure_one()
        error_msg = ""
        def post_message():
            email_template_id = self.env.ref('erpvn_attendance_device.email_template_attendance_device')
            self.post_message(email_template_id)
            self.env.cr.commit()

        try:
            self._set_zk()
            return self.zk.connect()
        except ZKNetworkError as e:
            error_msg = _("Could not reach the device %s (ping %s)") % (self.display_name, self.ip)
        except ZKConnectionUnauthorized as e:
            error_msg = _("Connection Unauthorized! The device %s may require password") % (self.display_name)
        except ZKErrorResponse as e:
            error_msg = _("Could not get connected to the device %s. This is usually due to either the network error or "
                "wrong protocol selection or password authentication is required.\nDebugging info:\n%s") % (self.display_name, e)
        except Exception as e:
            error_msg = _("Could not get connected to the device '%s'. Please check your network configuration and device password "
                "and/or hard restart your device") % (self.display_name,)

        if error_msg:
            post_message()
            raise ValidationError(error_msg)

    def disconnect(self):
        try:
            return self.zk.disconnect()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not get the device %s disconnected. Here is the debugging information:\n%s") % (self.display_name, e))

    def disable_device(self):
        """disable (lock) device, ensure no activity when process run"""
        try:
            return self.zk.disable_device()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not get the device %s disabled. Here is the debugging information:\n%s") % (self.display_name, e))

    def action_restart(self):
        self.ensure_one()
        self.restart_device()

    def enable_device(self):
        """re-enable the connected device"""
        try:
            return self.zk.enable_device()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the device %s enabled. Here is the debugging information:\n%s') % (self.display_name, e))

    def get_firmware_version(self):
        '''return the firmware version'''
        try:
            self.connect()
            self.enable_device()
            return self.zk.get_firmware_version()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not get the firmware version of the device %s. Here is the debugging information:\n%s") % (self.display_name, e))
        finally:
            self.disconnect()

    def get_serial_number(self):
        '''return the serial number'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_serialnumber()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not get the serial number of the device %s. Here is the debugging information:\n%s") % (self.display_name, e))
        finally:
            self.disconnect()

    def get_oem_vendor(self):
        '''return the serial number'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_oem_vendor()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the OEM Vendor of the device %s. Here is the debugging information:\n%s') % (self.display_name, e))
        finally:
            self.disconnect()

    def get_face_version(self):
        '''return the serial number'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_face_version()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the Face Version of the device %s. Here is the debugging information:\n%s') % (self.display_name, e))
        finally:
            self.disconnect()

    def get_fingerprint_version(self):
        '''return the serial number'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_fp_version()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the Fingerprint Version of the device %s. Here is the debugging information:\n%s') % (self.display_name, e))
        finally:
            self.disconnect()

    def get_finger_print_algorithm(self):
        '''return the Fingerprint Algorithm'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_fp_version()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the Fingerprint Algorithm of the device %s. Here is the debugging information:\n%s') % (self.display_name, e))
        finally:
            self.disconnect()

    def get_platform(self):
        '''return the serial number'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_platform()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the Platform of the device %s. Here is the debugging information:\n%s') % (self.display_name, e))
        finally:
            self.disconnect()

    def get_device_name(self):
        '''return the serial number'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_device_name()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the Name of the device %s. Here is the debugging information:\n%s') % (self.display_name, e))
        finally:
            self.disconnect()

    def get_workcode(self):
        '''return the serial number'''
        try:
            self.connect()
            self.enableDevice()
            return self.zk.get_workcode()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the Work Code of the device %s. Here is the debugging information:\n%s') % (self.display_name, e))
        finally:
            self.disconnect()

    def restart_device(self):
        '''restart the device'''
        try:
            self.connect()
            self.enable_device()
            return self.zk.restart()
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not get the serial number of the device %s. Here is the debugging information:\n%s') % (self.display_name, e))

    def set_device_user(self, uid=None, name='', privilege=0, password='', group_id='', user_id='', card=0):
        try:
            self.connect()
            self.enable_device()
            self.disable_device()
            return self.zk.set_user(uid, name, privilege, password, group_id, user_id, card)
        except Exception as e:
            _logger.info(e)
        finally:
            self.enable_device()
            self.disconnect()

    def delete_device_user(self, uid, user_id):
        '''delete specific user by uid'''
        try:
            self.connect()
            self.enable_device()
            self.disable_device()
            return self.zk.delete_user(uid, user_id)
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_('Could not delete the user with uid "%s", user_id "%s" from the device %s\n%s') % (uid, user_id, self.display_name, e))
        finally:
            self.enable_device()
            self.disconnect()

    def action_clear_data(self):
        pass # danger func
        # '''clear all data (include: user, attendance report, finger database )'''
        # try:
        #     self.connect()
        #     self.enable_device()
        #     self.disable_device()
        #     return self.zk.clear_data()
        # except Exception as e:
        #     _logger.error(e)
        #     raise ValidationError(_('Could not clear data from the device %s. Here is the debugging information:\n%s') % (self.display_name, e))
        # finally:
        #     self.enable_device()
        #     self.disconnect()

    def get_device_user(self):
        '''return a Python List of device users in User(uid, name, privilege, password, group_id, user_id)'''
        try:
            self.connect()
            self.enable_device()
            self.disable_device()
            return self.zk.get_users()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_('Could not get users from the device %s\nIf you had connected to your device, '
                'perhaps your device had problem. Some bad devices allowed duplicated uid may cause such problem. In such case, '
                'if you still want to load users from that bad device, please uncheck Data Acknowledge field.\n'
                'Here is the debugging error message:\n%s') % (self.display_name, str(e)))
        finally:
            self.enable_device()
            self.disconnect()

    def upload_finger_templates(self, uid, name, privilege, password, group_id, user_id, fingers):
        user = User(uid, name, privilege, password, group_id, user_id, card=0)
        try:
            self.connect()
            self.enable_device()
            self.disable_device()
            return self.zk.save_user_template(user, fingers)
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Could not set finger template into the device %s. Here are the information:\n"
                "user_id: %s\nDebugging information:\n%s") % (self.display_name, user_id, e))
        finally:
            self.enable_device()
            self.disconnect()

    def get_finger_template(self):
        '''return a Python List of fingers template in Finger(uid, fid, valid, template)'''
        try:
            self.connect()
            self.enable_device()
            self.disable_device()
            return self.zk.get_templates()
        except Exception as e:
            _logger.error(str(e))
            tries = 3
            if tries > 0:
                tries -= 1
                self.enable_device()
                self.disconnect()
                time.sleep(0.5)
                return self.get_finger_template()
            raise ValidationError(_('Could not get finger templates from the device %s\n'
                'If you had connected to your device, perhaps your device had problem. Some bad devices allowed '
                'duplicated uid may cause such problem. In such case, if you still want to load users from that '
                'bad device, please uncheck Data Acknowledge field.\nHere is the debugging error message:\n%s')
                % (self.display_name, str(e)))
        finally:
            self.enable_device()
            self.disconnect()

    def get_next_uid(self):
        '''return max uid of users on attendance device'''
        try:
            self.connect()
            self.enable_device()
            self.disable_device()
            return self.zk.get_next_uid()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_('Could not get max uid from the device %s\nIf you had connected to your device, '
                'perhaps your device had problem.\nHere is the debugging error message:\n%s') % (self.display_name, str(e)))
        finally:
            self.enable_device()
            self.disconnect()

    def _get_time_in_machine(self):
        try:
            self.connect()
            self.enable_device()
            return self.zk.get_time()
        except Exception as e:
            _logger.error(str(e))
            raise ValidationError(_("Could not get time from the device %s\nHere is the debugging error message:\n%s") % (self.display_name, str(e)))
        finally:
            self.disconnect()

    def _get_attendance_device(self):
        post_err_msg = False
        try:
            self.connect()
            self.enable_device()
            self.disable_device()
            return self.zk.get_attendance()
        except Exception as e:
            _logger.error(str(e))
            post_err_msg = True
            raise ValidationError(_('Could not get attendance data from the device %s') % (self.display_name))
        finally:
            if post_err_msg and self.download_error_notification:
                email_template_id = self.env.ref('erpvn_attendance_device.email_template_error_get_attendance')
                self.post_message(email_template_id)
            self.enable_device()
            self.disconnect()

    def clear_attendance(self):
        '''clear all attendance records from the device'''
        try:
            self.connect()
            self.enable_device()
            self.disable_device()
            return self.zk.clear_attendance()
        except Exception:
            raise ValidationError(_('Could not get attendance data from the device %s') % (self.display_name))
        finally:
            self.enable_device()
            self.disconnect()

    def _download_users_by_uid(self):
        """This method download and update all device users into model attendance.device.user using uid as key"""
        DeviceUser = self.env['attendance.device.user']
        for r in self:
            error_msg = ""
            device_users = r.get_device_user()

            uids = []
            for device_user in device_users:
                uids.append(device_user.uid)

            existing_user_ids = []

            device_user_ids = DeviceUser.with_context(active_test=False).search([('device_id', '=', r.id)])
            for user in device_user_ids.filtered(lambda user: user.uid in uids):
                existing_user_ids.append(user.uid)

            users_not_in_device = device_user_ids.filtered(lambda user: user.uid not in existing_user_ids)
            users_not_in_device.write({'not_in_device': True})

            for device_user in device_users:
                uid = device_user.uid
                vals = {
                    'uid': uid,
                    'name': device_user.name,
                    'privilege': device_user.privilege,
                    'password': device_user.password,
                    'user_id': device_user.user_id,
                    'device_id': r.id,
                }
                if device_user.group_id.isdigit():
                    vals['group_id'] = device_user.group_id
                if uid not in existing_user_ids:
                    try:
                        DeviceUser.create(vals)
                    except Exception as e:
                        _logger.info(e)
                        _logger.info(vals)
                        error_msg += str(e)
                        error_msg += _("\nData that caused the error: %s") % str(vals)
                else:
                    existing = DeviceUser.with_context(active_test=False).search([('uid', '=', uid), ('device_id', '=', r.id)], limit=1)
                    if existing:
                        update_data = {}
                        if existing.name != vals['name']:
                            update_data['name'] = vals['name']
                        if existing.privilege != vals['privilege']:
                            update_data['privilege'] = vals['privilege']
                        if existing.password != vals['password']:
                            update_data['password'] = vals['password']
                        if 'group_id' in vals and existing.group_id != vals['group_id']:
                            update_data['group_id'] = vals['group_id']
                        if existing.user_id != vals['user_id']:
                            update_data['user_id'] = vals['user_id']
                        if existing.device_id.id != vals['device_id']:
                            update_data['device_id'] = vals['device_id']
                        if bool(update_data):
                            try:
                                existing.write(update_data)
                            except Exception as e:
                                _logger.info(e)
                                _logger.info(vals)
                                error_msg += str(e) + "<br />"
                                error_msg += _("\nData that caused the error: %s") % str(
                                    update_data)
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

    def _download_users_by_user_id(self):
        """
        This method download and update all device users into model attendance.device.user using user_id as key
        NOTE: This method is experimental as it failed on comparing user_id in unicode type from devices (unicode: string) with user_id in unicode string from Odoo (u'string')
        """
        DeviceUser = self.env['attendance.device.user']
        for r in self:
            # device_users = User(uid, name, privilege, password, group_id, user_id)
            device_users = r.get_device_user()

            user_ids = []
            for device_user in device_users:
                user_ids.append(str(device_user.user_id))

            existing_user_ids = []
            device_user_ids = DeviceUser.with_context(
                active_test=False).search([('device_id', '=', r.id)])
            for user in device_user_ids.filtered(lambda user: user.user_id in user_ids):
                existing_user_ids.append(str(user.user_id))

            for device_user in device_users:
                user_id = str(device_user.user_id)
                vals = {
                    'uid': device_user.uid,
                    'name': device_user.name,
                    'privilege': device_user.privilege,
                    'password': device_user.password,
                    'user_id': device_user.user_id,
                    'device_id': r.id,
                }
                if device_user.group_id.isdigit():
                    vals['group_id'] = device_user.group_id
                if user_id not in existing_user_ids:
                    DeviceUser.create(vals)
                else:
                    existing = DeviceUser.with_context(active_test=False).search([
                        ('user_id', '=', user_id),
                        ('device_id', '=', r.id)], limit=1)
                    if existing:
                        existing.write(vals)

    def action_show_time(self):
        """Show the time on the machine"""
        self.ensure_one()
        raise ValidationError(_("The Machine time is %s") % self._get_time_in_machine())

    def action_user_download(self):
        """This method download and update all device users into model attendance.device.user"""
        for rec in self:
            if rec.unique_uid:
                rec._download_users_by_uid()
            else:
                rec._download_users_by_user_id()

    def action_user_upload(self):
        """
        This method will
        1. Download users from device
        2. Map the users with emloyee
        3. Upload users from model attendance.device.user into the device
        """
        ignored_employees_dict = {}
        for r in self:
            # Then we download and map all employees with users
            r.action_employee_map()
            # Then we create users from unmapped employee
            ignored_employees = []
            for employee in r.unmapped_employee_ids: # temporary for testing
                if not employee.barcode:
                    ignored_employees.append(employee)
                    continue
                employee.upload_user_attendance_device(r)
            # we download and map all employees with users again
            r.action_employee_map()

            if len(ignored_employees) > 0:
                ignored_employees_dict[r] = ignored_employees

        if not bool(ignored_employees_dict):
            message = _(
                'The following employees, who have no Badge ID defined, have not been uploaded to the corresponding device:\n')
            for device in ignored_employees_dict.keys():
                for employee in ignored_employees_dict[device]:
                    message += device.name + ': ' + employee.name + '\n'

            return {
                'warning': {
                    'title': "Some Employees could not be uploaded!",
                    'message': message,
                },
            }

    def action_employee_map(self):
        self.action_user_download()
        for r in self:
            for user in r.device_user_ids.filtered(lambda user: not user.employee_id): # temporary for testing
                employee = user.smart_find_employee()
                if employee:
                    user.write({'employee_id': employee})
            # upload users that are available in Odoo but not available in device
            # for user in r.device_user_ids.filtered(lambda user: user.not_in_device):
            #     user.set_device_user()

            # upload users that are available in Odoo but not available in device
            for user in r.device_user_ids.filtered(lambda user: user.not_in_device): # temporary for testing
                user.set_device_user()
                user.write({'not_in_device': False})

            if r.create_employee_during_mapping:
                users = r.device_user_ids.filtered(lambda user: not user.employee_id)
                if users:
                    users.generate_employees()
    
    def _prepare_attendance_vals(self, check, device_user, device, utc_dt):
        if check == 'check_in':
            res = {
                'employee_id': device_user.employee_id.id,
                'type': 'device',
                'check_in': utc_dt,
                'device_in_id': device.id,
                'state': 'no_check_out',
            }
        if check == 'check_out':
            res = {
                'employee_id': device_user.employee_id.id,
                'type': 'device',
                'check_in': utc_dt - timedelta(seconds=1),
                'device_in_id': False,
                'no_check_in': True,
                'state': 'no_check_in',
                'check_out': utc_dt,
                'device_out_id': device.id,
            }
        return res

    def _get_duplicated_domain_attendance(self, check, device_user, range):
        res = [('employee_id', '=', device_user.employee_id.id)]
        if check == 'check_out':
            res += [
                ('check_in', '>=', range.start_datetime),
                ('check_in', '<=', range.end_datetime),
                ('state', '=', 'no_check_out')

            ]
        elif check == 'check_in':
            res += [
                ('check_out', '>=', range.start_datetime),
                ('check_out', '<=', range.end_datetime),
                ('state', '=', 'no_check_in')
            ]
        elif check == 'system':
            res += [
                '&',
                    '|',
                        ('check_in', '>=', range.start_datetime),
                        ('check_in', '<=', range.end_datetime),
                        ('check_out', '=', False),
            ]
        return res

    def _check_existed_attendance(self, check, device_user, device, attendance_data):
        res = False
        hr_attendance_obj = self.env['hr.attendance']
        if hr_attendance_obj.search_count([
            '&',
                ('employee_id', '=', device_user.employee_id.id),
                '|',
                    ('check_in', '=', attendance_data.timestamp),
                    ('check_out', '=', attendance_data.timestamp),
            ]) > 0:
                res = True
        return res
    
    def _download_attendance(self, range_date, department_id=None, employee_id=None):
        device_user_obj = self.env['attendance.device.user']
        user_attendance_obj = self.env['user.attendance']
        hr_attendance_obj = self.env['hr.attendance']
        error_msg = ""

        for d in self.filtered(lambda x: x.map_before_dl):
            d.action_finger_template_download(department_id=None, employee_id=None)

        # state_type = {x.code: x.type for x in self.attendance_device_state_line_ids}
        attendance_data = []
        for device in self:
            device_data = list(filter(lambda x: x.user_id != '0' and x.timestamp >= range_date.start_datetime and x.timestamp <= range_date.end_datetime, device._get_attendance_device()))
            for d in device_data:
                d.device_id = device

            attendance_data += device_data
        attendance_data.sort(key=lambda t: t.timestamp)

        # convert device's timezone of attendance_data to utc.
        for atten in attendance_data:
            atten.timestamp = self.convert_time_to_utc(atten.timestamp, atten.device_id.tz).replace(tzinfo=None)

        domain = [('employee_id', '!=', False)]
        if employee_id:
            domain += [('employee_id', '=', employee_id.id)]
        elif department_id:
            domain += [('employee_id.department_id', '=', department_id.id)]

        for user_id in device_user_obj.with_context(active_test=False).search(domain):
            one_employee = list(filter(lambda x: x.user_id == user_id.user_id, attendance_data))
            for record in one_employee:
                if hr_attendance_obj.search_count([('employee_id', '=', user_id.employee_id.id),
                    '|', ('check_in', '=', record.timestamp), ('check_out', '=', record.timestamp)]) > 0:
                    continue

                att_checkin_id = hr_attendance_obj.search([('employee_id', '=', user_id.employee_id.id)], order='check_in desc')\
                    .filtered(lambda x: x.check_in and not x.check_out and \
                    record.timestamp > x.check_in and ((record.timestamp - x.check_in).total_seconds() / 3600) < self.env.company.limited_hours_between_in_out)

                if att_checkin_id:
                    att_checkin_id = att_checkin_id[0]

                if not att_checkin_id:
                    hr_attendance_obj.create(record.device_id._prepare_attendance_vals('check_in', user_id, record.device_id, record.timestamp))

                elif not att_checkin_id.check_out:
                    existed_in = self.convert_utc_time_to_tz(att_checkin_id.check_in, record.device_id.tz)
                    new_out = self.convert_utc_time_to_tz(record.timestamp, record.device_id.tz)
                    if new_out.date() > existed_in.date() and new_out.hour > 6:
                        hr_attendance_obj.create(record.device_id._prepare_attendance_vals('check_in', user_id, record.device_id, record.timestamp))
                        continue

                    att_checkin_id.update({
                        'state': 'draft',
                        'device_out_id': record.device_id.id,
                        'check_out': record.timestamp,
                    })

        for attendance in attendance_data:
            if attendance.timestamp in range_date:
                user_id = device_user_obj.with_context(active_test=False).search([('employee_id', '=', False), ('user_id', '=', attendance.user_id)], limit=1)
                if user_id:
                    if user_attendance_obj.search_count([
                        ('device_id', '=', attendance.device_id.id),
                        ('user_id', '=', user_id.id),
                        ('timestamp', '=', attendance.timestamp)]) > 0:
                        continue

                    vals = {
                        'device_id': attendance.device_id.id,
                        'user_id': user_id.id,
                        'timestamp': attendance.timestamp,
                    }

                    user_attendance_obj.create(vals)

        self.write({'last_attendance_download': fields.Datetime.now()})

        for d in self:
            if error_msg and d.debug_message:
                d.message_post(body=error_msg)

            if d.auto_clear_attendance:
                if d.auto_clear_attendance_schedule == 'on_download_complete':
                    d.action_attendance_clear()
                elif d.auto_clear_attendance_schedule == 'time_scheduled':
                    # datetime in the timezone of the device
                    dt_now = d.convert_utc_time_to_tz(datetime.utcnow(), d.tz)
                    float_dt_now = d.time_to_float_hour(dt_now)

                    if d.auto_clear_attendance_dow == '-1' or str(dt_now.weekday()) == d.auto_clear_attendance_dow:
                        delta = d.auto_clear_attendance_hour - float_dt_now
                        if abs(delta) <= 0.5 or abs(delta) >= 23.5:
                            d.action_attendance_clear()

    def action_attendance_download(self, range_date=None, department_id=None, employee_id=None):
        if not range_date:
            range_date = DateTimeRange(fields.Datetime.today() - timedelta(hours=self.env.company.limited_hours_to_get_attendances), fields.Datetime.today())
        
        # for device in self:
        self._download_attendance(range_date, department_id, employee_id)

    def action_finger_template_download(self, department_id=None, employee_id=None):
        finger_template_obj = self.env['finger.template']
        device_user_obj = self.env['attendance.device.user']
        for r in self:
            r.action_employee_map()
            device_users = device_user_obj.search([('device_id', '=', r.id)])

            # if there is still no device users, just ignore downloading finger templates
            if not device_users:
                continue

            template_data = r.get_finger_template()
            template_datas = []
            for template in template_data:
                template_datas.append(str(template.uid) + '_' + str(template.fid))

            existed_finger_lst = []
            finger_template_ids = finger_template_obj.search([('device_id', '=', r.id)])
            for template in finger_template_ids.filtered(lambda tmp: (str(tmp.uid) + '_' + str(tmp.fid)) in template_datas):
                existed_finger_lst.append(str(template.uid) + '_' + str(template.fid))

            vals_list = []
            for template in template_data:
                device_user_id = device_user_obj.search([('uid', '=', template.uid), ('device_id', '=', r.id)], limit=1)
                device_user_id = device_users.filtered(lambda u: u.uid == template.uid)
                if not device_user_id or (employee_id and device_user_id and device_user_id.employee_id.id != employee_id.id) or \
                    (department_id and device_user_id and device_user_id.employee_id.department_id.id != employee_id.department_id.id):
                    continue

                device_user_id = device_user_id[0]
                vals = {
                    'device_user_id': device_user_id.id,
                    'fid': template.fid,
                    'valid': template.valid,
                    'template': template.template,
                }
                if device_user_id.employee_id:
                    vals['employee_id'] = device_user_id.employee_id.id

                if device_user_id.user_id != device_user_id.employee_id.barcode:
                    continue

                if (str(template.uid) + '_' + str(template.fid)) not in existed_finger_lst:
                    vals_list.append(vals)
                else:
                    existing = finger_template_obj.search([('uid', '=', template.uid), ('fid', '=', template.fid), ('device_id', '=', r.id)], limit=1)
                    if existing and existing.device_user_id.user_id == device_user_id.employee_id.barcode:
                        existing.write(vals)
            if vals_list:
                finger_template_obj.create(vals_list)
        return

    def is_attendance_clear_safe(self):
        """If the data from devices has not been downloaded into Odoo, this method will return false"""
        hr_attendance_obj = self.env['hr.attendance']
        device_user_obj = self.env['attendance.device.user']
        check_statuses = self.attendance_device_state_line_ids.mapped('code')

        attendances = self._get_attendance_device()  # Attendance(user_id, timestamp, status)
        for att in attendances:
            if att.punch not in check_statuses:
                continue
            user = device_user_obj.with_context(active_test=False).search([('user_id', '=', att.user_id), ('device_id', '=', self.id)], limit=1)
            utc_dt = self.convert_time_to_utc(att.timestamp, self.tz)
            str_utc_dt = fields.Datetime.to_string(utc_dt)
            match = hr_attendance_obj.search([('device_user_id', '=', user.id),
                ('status', '=', att.punch), '|', ('check_in', '=', str_utc_dt), ('check_out', '=', str_utc_dt)], limit=1)
            if not match:
                return False, att
        return True, False

    def action_attendance_clear(self):
        """Method to clear all attendance data from the device"""
        for r in self:
            error_msg = ""
            attendance_clear_safe, att = r.is_attendance_clear_safe()
            if attendance_clear_safe:
                r.clear_attendance()
            else:
                error_msg += _("It was not safe to clear attendance data from the device %s.<br />The following "
                    "attendance data has not been stored in Odoo yet:<br />user_id: %s<br />timestamp: %s<br />"
                    "status: %s<br />") % (r.name, att.user_id, att.timestamp, att.punch)
                _logger.warning("It was not safe to clear attendance data from the device %s" % r.name)
                if r.auto_clear_attendance_error_notif:
                    email_template_id = self.env.ref('erpvn_attendance_device.email_template_not_safe_to_clear_attendance')
                    r.post_message(email_template_id)
            if error_msg and r.debug_message:
                r.message_post(body=error_msg)

    def action_check_connection(self):
        self.ensure_one()
        if self.connect():
            self.disconnect()
            raise UserError(_('Connect to the device %s successfully') % (self.display_name))

    def action_device_information(self):
        dbname = self._cr.dbname
        for r in self:
            try:
                cr = registry(dbname).cursor()
                r = r.with_env(r.env(cr=cr))
                r.connect()
                r.firmware_version = r.zk.get_firmware_version()
                r.serialnumber = r.zk.get_serialnumber()
                r.platform = r.zk.get_platform()
                r.device_name = r.zk.get_device_name()
                r.work_code = r.zk.get_workcode()
                r.face_version = r.zk.get_face_version()
                r.fingerprint_version = r.zk.get_fp_version()
                r.oem_vendor = r.zk.get_oem_vendor()
            except Exception as e:
                _logger.error(e)
            finally:
                cr.commit()
                cr.close()

    @api.model
    def post_message(self, email_template):
        if self.user_id:
            self.message_subscribe([self.user_id.partner_id.id])
        if email_template:
            self.message_post_with_template(email_template.id)

    def action_view_users(self):
        action = self.env.ref('erpvn_attendance_device.device_user_list_action')
        result = action.read()[0]
        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        if self.device_users_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.device_user_ids.ids) + ")]"
        else:
            res = self.env.ref('erpvn_attendance_device.attendance_device_user_form_view', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.device_user_ids.id
        return result

    def action_view_attendance_data(self):
        self.ensure_one()
        action = self.env.ref('hr_attendance.hr_attendance_action')
        result = action.read()[0]
        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        total_att_records = self.env['hr.attendance'].search_count(['|', ('device_in_id', '=', self.id), ('device_out_id', '=', self.id)])
        if total_att_records > 1:
            result['domain'] = ['|', ('device_in_id', 'in', self.ids), ('device_out_id', 'in', self.ids)]
        elif total_att_records == 1:
            res = self.env.ref('hr_attendance.hr_attendance_view_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.env['hr.attendance'].search(['|', ('device_in_id', '=', self.id), ('device_out_id', '=', self.id)]).id
        return result

    def action_view_mapped_employees(self):
        action = self.env.ref('hr.open_view_employee_list_my')
        result = action.read()[0]
        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        if self.mapped_employees_count != 1:
            result['domain'] = "[('id', 'in', " + str(self.mapped_employee_ids.ids) + ")]"
        else:
            res = self.env.ref('erpvn_attendance_device.view_employee_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.mapped_employee_ids.id
        return result

    def action_view_finger_template(self):
        self.ensure_one()
        action = self.env.ref('erpvn_attendance_device.action_finger_template')
        result = action.read()[0]
        # reset context
        result['context'] = {}
        # choose the view_mode accordingly
        if self.finger_template_count != 1:
            result['domain'] = "[('device_id', 'in', " + str(self.ids) + ")]"
        else:
            res = self.env.ref('erpvn_attendance_device.view_finger_template_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.finger_template_ids.id
        return result

    def unlink(self):
        force_delete = self.env.context.get('force_delete', False)
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You cannot delete the device '%s' while its state is not Draft.") % (rec.display_name))
            if rec.device_user_ids and not force_delete:
                raise UserError(_("You may not be able to delete the device '%s' while its data is stored in Odoo. "
                    "Please remove all the related data of this device before removing it from Odoo. You may also consider "
                    "to deactivate this device so that you don't have to delete it.") % (rec.display_name))
        return super(AttendanceDevice, self).unlink()


class AttendanceDeviceStateLine(models.Model):
    _name = 'attendance.device.state.line'
    _description = 'Attendance Device State'

    attendance_state_id = fields.Many2one('attendance.state', string='State Code', required=True, index=True)
    device_id = fields.Many2one('attendance.device', string='Device', required=True, ondelete='cascade', index=True, copy=False)
    code = fields.Integer(string='Code Number', related='attendance_state_id.code', store=True)
    type = fields.Selection(related='attendance_state_id.type', store=True)
    work_entry_type_id = fields.Many2one('hr.work.entry.type', related='attendance_state_id.work_entry_type_id', store=True)

    _sql_constraints = [
        ('attendance_state_id_device_id_unique', 'UNIQUE(attendance_state_id, device_id)', 'The Code must be unique per Device'),
    ]