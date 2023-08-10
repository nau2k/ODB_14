# -*- coding: utf-8 -*-
import logging
from datetime import timedelta, datetime
from odoo.exceptions import ValidationError, UserError
from odoo.tools import ustr
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')
try:
    import xlrd
except ImportError:
    _logger.debug('Cannot `import xlrd`.')

col_names = [
    'Badge ID', 'Employee', 'Check In', 'Check Out',
] 

class UpdateAttendanceWizard(models.TransientModel):
    _name = 'attendance.update.wizard'
    _description = 'Attendance Update Wizard'

    name = fields.Char(string='name')
    date_upload = fields.Char(string='Date From',default = '00:00:00')
    option = fields.Selection(string='Option', selection=[('insert time', 'Insert Time'),
        ('add full', 'Add Full Attendances'),
        ('delete','Delete Attendances'),
        ('import','Import Attendances'),
        ],default='insert time')

    day_from = fields.Date(string='Date From')
    day_to = fields.Date(string='Date To')
    employee_ids = fields.Many2many('hr.employee', string="Employees")
    resource_calendar_id = fields.Many2one('resource.calendar', 'Working Schedule')
    # attendance_id = fields.Many2one('resource.calendar.attendance', string='Work Detail', store=True)
    line_ids = fields.One2many('attendance.update.line.wizard','wizard_id',string='Attendances Lines',)

    file = fields.Binary('File')
    import_option = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')],string='Select',default='xls')

    @api.onchange('date_upload')
    def _onchange_date_upload(self):
        for rec in self.date_upload:
            if rec.islower():
                raise ValidationError(_('The time entered contains letters, please double check'))

    def action_update_attendances(self):
        base_obj = self.env['erpvn.base']

        # Tính toán lại giá trị của fields date_upload
        date_upload = datetime.strptime(self.date_upload, "%H:%M:%S")
        date_convert = date_upload - datetime(1900, 1, 1)
        MinutesGet, SecondsGet = divmod(date_convert.seconds, 60)
        HoursGet, MinutesGet = divmod(MinutesGet,60)

        for line in self.line_ids:
            # Lấy ra ngày tháng năm của attendance(line)
            # datetime.datetime(2022,06,15,17,24,00) -> datetime.datetime(2022,06,15,0 0)
            day_attendance = line.check_in.strftime('%Y:%m:%d')
            date_attendance = datetime.strptime(day_attendance, "%Y:%m:%d")

            # Tạo thêm một điểm thời gian để cập nhật lại danh sách 
            add_date = date_attendance + timedelta(hours =HoursGet, minutes=MinutesGet, seconds=SecondsGet)
            utc_dt =base_obj.convert_time_to_utc(add_date, line.employee_id.tz).replace(tzinfo=None)

            # Lọc dữ liệu theo attendance và sắp xếp lại danh sách 
            attendances=self.env['hr.attendance'].search([('employee_id','=',line.employee_id.id),
                '|', ('check_in','>=',line.check_in), ('check_out','>=',line.check_out)])
            lits_attendances=attendances.filtered(lambda x: x.check_in !=False and x.check_out != False)
            list_att=(lits_attendances.mapped('check_in')+lits_attendances.mapped('check_out'))
            list_att.append(utc_dt)
            list_att.sort()

            i = 0
            for rec in lits_attendances:
                rec.update({
                    'check_in':list_att[i],
                    'check_out':list_att[i+1],
                })
                i+=2

    def _get_valid_working_shifts(self):
        return self.env['resource.calendar'].search([])

    def update_attendances_all(self):
        self.ensure_one()
        
        object_hr_attendances = self.env['hr.attendance']
        base_obj = self.env['erpvn.base']
        date_total= (self.day_to -self.day_from).days

        
        if self.resource_calendar_id.id in self._get_valid_working_shifts().ids:
            date_from =[]
            date_to =[]
            
            attendances= self.resource_calendar_id.attendance_ids
            for line in attendances:
                if line.name in['Monday','Tuesday','Wednesday','Thursday','Friday']:
                    date_from.append(attendances[0].hour_from)
                    date_to.append(attendances[0].hour_to)
                else:
                    date_from.append(line.hour_from)
                    date_to.append(line.hour_to)

            date_from = list(set(date_from))
            date_to = list(set(date_to))

            from_convert = str(timedelta(hours=date_from[0]))
            to_convert = str(timedelta(hours=date_to[0]))
            check_out_saturday =  str(timedelta(hours=date_to[1]))

            # chuyển qua giờ , phút giây các giá trị  ( check in, check out, check out ngày thứ bảy)
            date_upload = datetime.strptime(from_convert, "%H:%M:%S")
            date_convert = date_upload - datetime(1900, 1, 1)
            MinutesGet_from, SecondsGet_from = divmod(date_convert.seconds, 60)
            HoursGet_from, MinutesGet_from = divmod(MinutesGet_from,60)

            date_upload2 = datetime.strptime(to_convert, "%H:%M:%S")
            date_convert2 = date_upload2 - datetime(1900, 1, 1)
            MinutesGet_to, SecondsGet_to = divmod(date_convert2.seconds, 60)
            HoursGet_to, MinutesGet_to = divmod(MinutesGet_to,60)

            date_upload3 = datetime.strptime(check_out_saturday, "%H:%M:%S")
            date_convert3 = date_upload3 - datetime(1900, 1, 1)
            Mi_saturday, Se_saturday = divmod(date_convert3.seconds, 60)
            Hour_saturday, Mi_saturday = divmod(Mi_saturday,60)
            
            #lấy ra ngày bắt đầu để khỏi tạo danh sách "datetime.datetime(2022,6,14,0,0)"
            day_from = datetime.combine(self.day_from, datetime.min.time())

            list_attendances=[]
            for employee in self.employee_ids:
                convert_check_in = day_from + timedelta(hours= HoursGet_from, minutes=MinutesGet_from ,seconds= SecondsGet_from)
                convert_check_out = day_from + timedelta(hours= HoursGet_to, minutes=MinutesGet_to ,seconds= SecondsGet_to)
                
                check_in =base_obj.convert_time_to_utc(convert_check_in, employee.tz).replace(tzinfo=None)
                check_out =base_obj.convert_time_to_utc(convert_check_out, employee.tz).replace(tzinfo=None)
                
                for day in range(0, date_total + 1):
                    if check_in.strftime('%A')=='Sunday':
                        check_in += timedelta(hours=24)
                        check_out += timedelta(hours=24)
                        continue
                    else:
                        atten = object_hr_attendances.create({
                                'employee_id': employee.id,
                                'employee_barcode': employee.barcode,
                                'check_in': check_in,
                                'check_out': check_out,
                                'state': 'draft',
                        })
                        list_attendances.append(atten)
                    check_in += timedelta(hours=24)
                    check_out += timedelta(hours=24)

            # cập nhật lại giờ check out đối với trường hợp là thứ bảy.
            for rec in list_attendances:
                if rec.check_in.strftime('%A')=='Saturday':
                    day_attendance = rec.check_out.strftime('%Y:%m:%d')
                    date_attendance = datetime.strptime(day_attendance, "%Y:%m:%d")
                    check_out_convert= date_attendance + timedelta(hours= Hour_saturday, minutes=Mi_saturday ,seconds= Se_saturday)
                    check_out = base_obj.convert_time_to_utc(check_out_convert, rec.employee_id.tz).replace(tzinfo=None)
                    rec.update({
                        'check_out':check_out
                    })   
            return list_attendances

    def delete_attendaces(self):
        for line in self.employee_ids:
            list_attendace = self.env['hr.attendance'].search([('employee_id','=',line.id),('check_in','>=',self.day_from),('check_out','<=',self.day_to)])
        return list_attendace.unlink()

    def read_xls_book(self):
        book = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
        try:
            sheet = book.sheet_by_name("Attendances")
        except Exception as e:
            raise UserError(_(e))
        values_sheet = []
        for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
            if all(str(e.value).strip() == '' for e in row):
                continue
            values = []
            for colx, cell in enumerate(row, 1):
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(
                        str(cell.value)
                        if is_float
                        else str(int(cell.value))
                    )
                elif cell.ctype is xlrd.XL_CELL_DATE:
                    values.append(datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode)))
                elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                    values.append(u'True' if cell.value else u'False')
                elif cell.ctype is xlrd.XL_CELL_ERROR:
                    raise ValueError(
                        _("Invalid cell value at row %(row)s, column %(col)s: %(cell_value)s") % {
                            'row': rowx,
                            'col': colx,
                            'cell_value': xlrd.error_text_from_code.get(cell.value, _("unknown error code %s") % cell.value)
                        }
                    )
                else:
                    if '\n' in cell.value:
                        val = ''.join(cell.value.split('\n'))
                    else:
                        val = cell.value
                    values.append(str(val).strip())
            values_sheet.append(values)
        return values_sheet

    def get_values(self, row, col_name, col_index):
        name_key = [col_name[i] for i in col_index]
        value_key = [row[j] for j in col_index]
        return dict(zip(name_key , value_key ))

    def import_excel(self):
        if not self.file:
            raise UserError(_("Please, upload your excel file or download a sample file below."))

        values = self.read_xls_book()

        if len(values) < 1:
            raise UserError(_("The file is empty."))

        counter = 1
        skip_header = True
        skipped_line_no = {}
        col_index = [values[0].index(a) for a in col_names]

        attendance_obj = self.env['hr.attendance']
        employee_obj = self.env['hr.employee']
        base_obj = self.env['erpvn.base']

        attendance_vals = []
        for row in values:
            try:
                if skip_header:
                    skip_header = False
                    counter = counter + 1
                    continue

                val = self.get_values(row, values[0], col_index)

                if val.get('Badge ID', '') in (None, ''):
                    skipped_line_no[str(counter)] = _(" - Badge ID column is not valid.")
                    counter = counter + 1
                    continue

                employee_id = employee_obj.search([('barcode', '=', val['Badge ID'])])
                if not employee_id:
                    skipped_line_no[str(counter)] = _(" - Not found employee with Badge ID '%s'." % str(val['Badge ID']))
                    counter = counter + 1
                    continue
                
                check_in = check_out = False

                if val['Check In']:
                    check_in = base_obj.convert_time_to_utc(val['Check In']).replace(tzinfo=None)

                if val['Check Out']:
                    check_out = base_obj.convert_time_to_utc(val['Check Out']).replace(tzinfo=None)

                if check_in and check_out:
                    if check_out < check_in:
                        skipped_line_no[str(counter)] = _('"Check Out" time cannot be earlier than "Check In" time.')
                        counter = counter + 1
                        continue

                attendance_vals.append({
                    'employee_id': employee_id.id,
                    'check_in': check_in,
                    'check_out': check_out,
                })
                counter += 1
            except Exception as e:
                dic_msg = ''
                if skipped_line_no:
                    dic_msg = dic_msg + "Errors (%s):" % str(len(skipped_line_no) + 1) # add 1 sourcecode error.
                    for k, v in skipped_line_no.items():
                        dic_msg = dic_msg + "\nRow. " + k + v
                dic_msg = dic_msg + _("\nRow. " + str(counter) + " - SourceCodeError: " + ustr(e))
                raise ValidationError(dic_msg)

        attendance_obj.create(attendance_vals)

        created_num = 0
        message = ''
        if counter > 1:
            created_num = counter - len(skipped_line_no) - 1
            message = str(created_num) + " Records imported successfully."
            if skipped_line_no:
                message = message + "\nErrors (%s):" % str(len(skipped_line_no))
            for k, v in skipped_line_no.items():
                message = message + "\nRow. " + k + v

        message_id = self.env['message.wizard'].create({'message': message})
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.wizard',
            'res_id': message_id.id,
            'target': 'new'
                }


class UpdateAttendanceWizardLine(models.TransientModel):
    _name = 'attendance.update.line.wizard'
    _description = 'Attendance Update Line Wizard'

    # utc_dt = base_obj.convert_utc_time_to_tz(self.date_upload, self.tz).replace(tzinfo=None)
    wizard_id = fields.Many2one('attendance.update.wizard')
    employee_barcode = fields.Char(related='employee_id.barcode', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    check_in = fields.Datetime(string="Check In", required=True)
    device_in_id = fields.Many2one('attendance.device', string='Device In', help='The device with which user took check in action')
    check_out = fields.Datetime(string="Check Out")
    device_out_id = fields.Many2one('attendance.device', string='Device Out', help='The device with which user took check out action')
    worked_hours = fields.Float(string='Worked Hours', store=True, readonly=True)
    attendance_late = fields.Integer(string="Late (Minutes)", default=0.0, readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('cancelled', 'Cancelled'), ('approve', 'Approved'),
        ('no_check_in', 'No Check-In'), ('no_check_out', 'No Check-Out')], string='Status', required=True,default='draft')
