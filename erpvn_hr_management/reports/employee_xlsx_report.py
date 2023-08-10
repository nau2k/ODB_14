# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import date, timedelta
import logging
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

_logger = logging.getLogger(__name__)

                        
class Exportemployee(models.AbstractModel):
    _name = "report.erpvn_hr_management.export_employee"
    _description = "Report Sale Order"
    _inherit = "report.report_xlsx.abstract"


    def get_action(self, data):
        module = __name__.split("addons.")[1].split(".")[0]
        report_name = "{}.export_employee".format(module)
        report_file = 'List Employee'
        return {
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "report_name": report_name,
            "context": dict(self.env.context),
            "data": dict(data=data,report_file=report_file),
            }

    def get_resignation_reason(self,employee):
        resign = self.env['hr.resignation'].search([('employee_id.id','=',employee.id)])
        if resign:
            return resign.reason
        else: return ''
            
    def get_translate_value(self,record):
        name = record._name+','+'name'
        result = self.env['ir.translation'].search([('src','=',record.name),('name','=',name),('lang','=','vi_VN')]).value or self.env['ir.translation']
        if result:
            return result
        else: 
            return record.name

    def generate_xlsx_report(self, workbook, data, obj):
        workbook.set_properties({"comments": "Created with Python and XlsxWriter from Odoo"})
        if not isinstance(data.get('data'), str):
            list_employee = self.env['hr.employee'].browse(data.get('data').get('ids')) or obj
        else:
            list_employee = obj
        num_format_currency = "#,##0"
        format_currency = workbook.add_format( {'num_format':num_format_currency})
        title_style = workbook.add_format(
            {"bold": True, "bg_color": "#FFFFCC", "bottom": 1,"top":1,"right":1,"left":1,'align':'center','text_wrap': True,'valign':'vcenter',}
        )
        red = workbook.add_format(
            {"bold": True,"bg_color": "#ff1c62", "bottom": 1,'align': 'center','text_wrap': True,'valign':'vcenter',}
        )
        white = workbook.add_format(
            {"bold": True,"bg_color": "white","bottom": 1,"top":1,"right":1,"left":1,'align': 'center','text_wrap': True,'valign':'vcenter',}
        )
        grey = workbook.add_format(
            {"bold": True,"bg_color": "a2a2a2", "bottom": 1,'align': 'center','text_wrap': True,'valign':'vcenter',}
        )
        yellow = workbook.add_format(
            {"bold": True,"bg_color": "#dddf00", "bottom": 1,'align': 'center','text_wrap': True,'valign':'vcenter',}
        )
        blue = workbook.add_format(
            {"bold": True,"bg_color": "#3fb5e6", "bottom": 1,'align': 'center','text_wrap': True,'valign':'vcenter',}
        )
        dark_blue = workbook.add_format(
            {"bold": True,"bg_color": "#3a5eed", "bottom": 1,'align': 'center','text_wrap': True,'valign':'vcenter',}
        )
        violet = workbook.add_format(
            {"bold": True,"font_color":'#8623c3', "bottom": 1,'align': 'center','text_wrap': True,'valign':'vcenter',}
        )   
        date_format = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy'})
        #0854ff
        sheet = workbook.add_worksheet(_("List Employee"))
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(80)
        sheet.set_column(0, 0, 5)
        sheet.set_column(1,1,10)
        sheet.set_column(2,2,30)
        sheet.set_column(3,3,40)
        sheet.set_column(4,4,40)
        sheet.set_column(5,5,40)
        sheet.set_column(6,6,40)
        sheet.set_column(7,7,8)
        sheet.set_column(8,8,25)
        sheet.set_column(9,9,15)
        sheet.set_column(10,10,15)
        sheet.set_column(11,11,15)
        sheet.set_column(12,12,15)
        sheet.set_column(13,13,15)
        sheet.set_column(14,14,40)
        sheet.set_column(15,15,15)
        sheet.set_column(16,16,16)
        sheet.set_column(17,17,15)
        sheet.set_column(18,18,25)
        sheet.set_column(19,19,15)
        sheet.set_column(20,20,15)
        sheet.set_column(21,21,15)
        sheet.set_column(22,22,15)
        sheet.set_column(23,23,15)
        sheet.set_column(24,24,15)
        sheet.set_column(25,25,15)
        sheet.set_column(26,26,15)
        sheet.set_column(27,27,15)
        sheet.set_column(28,28,15)
        sheet.set_column(29,29,40)
        sheet.set_column(30,30,40)
        sheet.set_column(31,31,40)
        sheet.set_column(32,32,15)
        sheet.set_column(33,33,15)
        sheet.set_column(34,34,15)
        sheet.set_column(35,35,15)
        sheet.set_column(36,36,15)
        sheet.set_column(37,37,15)
        sheet.set_column(38,38,15)
        sheet.set_column(39,39,15)
        sheet.set_column(40,40,25)
        sheet.set_column(41,41,15)
        sheet.set_column(42,42,15)
        sheet.set_column(43,43,15)
        sheet.set_column(44,44,29)
        sheet.set_column(45,45,15)
        sheet.set_column(46,46,20)
        sheet.set_column(47,47,15)
        sheet.set_column(48,48,20)
        sheet.set_column(49,49,15)
        sheet.set_column(50,50,15)
        sheet.set_column(51,51,15)
        sheet.set_column(52,52,40)
        sheet.set_column(53,53,8)
        sheet.set_column(54,54,15)
        sheet.set_column(55,55,15)
        sheet.set_column(56,56,40)
        sheet.set_column(57,67,15)
        sheet.set_column(58,58,15)
        sheet.set_column(59,59,15)
        sheet.set_column(60,60,40)
        sheet.set_column(61,61,15)
        sheet.set_column(62,62,15)
        sheet.set_column(63,63,30)
        sheet.set_column(64,64,30)
        sheet.set_column(65,65,30)
        sheet.set_column(66,66,30)
        sheet.set_column(67,67,30)
        sheet.set_column(68,68,30)
        sheet.set_column(69,69,10)
        sheet.set_column(70,70,15)
        sheet.set_column(71,71,15)
        sheet.set_column(72,72,15)
        sheet.set_column(74,73,15)
        sheet_title = [
            _("STT"),
            _("MSNV"),
            _("Họ và tên viết in"),
            _("chức danh (title)"),
            _("Position"),
            _("Phòng ban"),
            _("Dept."),
            _("Code"),
            _("Nơi làm việc."),
            _("Ngày bắt đầu"),
            _("Ngày kết thúc"),
            _("Lý do nghỉ việc"),

            _("HĐLĐ từ"),
            _("HĐLĐ đến"),
            _("Loại HĐ"),
            _("Mã HĐ"),
            _("Số nội bộ"),
            _("Điện thoại di động"),
            _("Địa chỉ email"),
            _("Mail cá nhân"),
            _("Số CMTND"),
            _("Ngày cấp"),
            _("Nơi cấp"),
            _("Ngày tháng năm sinh"),
            _("Nơi sinh"),
            _("Giới tính"),
            _("Dân tộc"),

            _("Nguyên quán"),
            _("Trình độ học vấn"),
            _("Địa chỉ thường trú"),
            _("Địa chỉ Liên lạc"),
            _("Lương thử việc"),
            _("Phụ cấp trách nhiệm"),
            _("Lương 2016"),
            _("Lương sau thử việc"),
            _("Lương căn bản"),
            _("Thưởng hoàn thành công việc"),
            _("Phụ cấp trách nhiệm"),
            _("KCBBĐ"),
            _("Trình độ chuyên môn"),

            _("Số TK"),
            _("Mã số thuế"),
            _("Số người phụ thuộc"),
            _("Thời gian gia nhập công đoàn"),
            _("Họ tên con"),
            _("Ngày tháng năm sinh"),
            _("Họ tên con"),
            _("Ngày tháng năm sinh"),
            _("Họ tên con"),
            _("Ngày tháng năm sinh"),

            _("HĐLĐ lần 1 từ"),
            _("HĐLĐ lần 1 đến"),
            _("Loại HĐ"),
            _("Mã HĐ"),
            _("HĐLĐ lần 2 từ"),
            _("HĐLĐ lần 2 đến"),
            _("Loại HĐ"),
            _("Mã HĐ"),
            _("HĐLĐ lần 3 từ"),
            _("số thứ tự HĐ"),
            _("Loại HĐ"),
            _("Mã HĐ"),
            _("Số tháng làm việc"),

            _("Nhân viên (Mẫu KPI, 1 lần/tháng) VND"),
            _("Nhân viên (Mẫu KPI, 1 lần/tháng) USD"),
            _("Quản lý (mẫu PMP 1 lần/năm) VND"),
            _("Quản lý (mẫu PMP 1 lần/năm) USD"),
            _("Đào tạo (Mẫu Trainer, 2 lần/năm) VND"),
            _("Đào tạo (Mẫu Trainer, 2 lần/năm) USD"),
            _("Số sổ BHXH"),
            _("Nơi đăng ký KCB"),
            _("Số thẻ KCB"),
            _("Ngày tham gia BHXH, YT, TN"),
        ]
        sheet_title_eng = [
            _("No"),
            _("Staff Code"),
            _(""),
            _("Job title"),
            _(""),
            _("Team"),
            _(""),
            _("Working Place"),
            _(""),
            _("Starting Date"),
            _("End Date"),
            _("Resignation Reason"),

            _("Current Contract"),
            _(""),
            _(""),
            _(""),
            _("Ext"),
            _("mobile Phone"),
            _("Email add"),
            _(""),
            _("ID Number"),
            _("Issued Date"),
            _("Issued Place"),
            _("Date of birth"),
            _("Place of birth"),
            _("Gender"),
            _("National"),

            _("Home village"),
            _("Education"),
            _("Home address"),
            _("Permanent address"),
            _("Probation Salary"),
            _(""),
            _("Salary 2016"),
            _("Total Salary"),
            _("Basic Salary"),
            _("Allowance"),
            _(""),
            _("Khám chữa bệnh ban đầu"),
            _(""),

            _("Number"),
            _("Tax code"),
            _("Independents"),
            _("Labor Union"),
            _(""),
            _(""),
            _(""),
            _(""),
            _(""),
            _(""),

            _("The first contract"),
            _(""),
            _(""),
            _(""),
            _("The second contract"),
            _(""),
            _(""),
            _(""),
            _("The third contract"),
            _(""),
            _(""),
            _(""),
            _("working month"),

            _("Agent (KPI form, once/month)"),
            _("Agent (KPI form, once/month)"),
            _("Managers (PMP form,once/year) VND"),
            _("Managers (PMP form,once/year) USD"),
            _("Trainer (Trainer,form,twice/year) VND"),
            _("Trainer (Trainer,form,twice/year) USD"),
            _("SI number"),
            _("Registry place"),
            _("Health card No"),
            _("Joined date in insurances"),
        ]
        sheet_number =[i for i in range(1,74)]
        sheet.write_row(0, 0, sheet_number)
        # line 1
        sheet.set_row(0, None, None, {"collapsed": 1})
        # line 2
        sheet.set_row(2,25)
        sheet.merge_range('A2:P2', 'Work', grey)
        sheet.merge_range('Q2:T2', 'Internal', red)
        sheet.merge_range('U2:AE2', 'Base', yellow)
        sheet.merge_range('AF2:AX2', 'Salary', red)
        sheet.merge_range('AY2:BK2', 'HĐ Lao Dong', dark_blue)
        sheet.merge_range('BL2:BQ2', 'Work', white)
        sheet.merge_range('BR2:BU2', 'So Lao Dong', blue)
        # line 3
        sheet.merge_range('C3', 'Staff  information', white)
        sheet.merge_range('D3:I3', 'Work information', white)
        sheet.merge_range('J3:S3', 'Labour Contract', white)
        sheet.merge_range('U3:W3', 'ID details', white)
        sheet.merge_range('X3:AE3', 'Personal information', white)
        sheet.merge_range('AF3:AL3', 'Salary', white)
        sheet.merge_range('AR3', 'Bank Details', white)
        sheet.merge_range('AP3:AQ3', 'Family condition deduction', white)
        sheet.merge_range('AR3:AX3', '', white)
        sheet.merge_range('AY3:BK3', 'Labour Contract', white)
        sheet.merge_range('BL3:BQ3', 'Perfomance Evaluation', white)
        sheet.write(2,69,'Social insurance', white)
        sheet.merge_range('BS3:BU3', 'Health insurance', white)
        # line 4
        sheet.set_row(3,30)
        sheet.merge_range('C4', 'Thông tin nhân viên', white)
        sheet.merge_range('D4:I4', 'Thông tin công việc', white)
        sheet.merge_range('J4:S4', 'Thông tin Hợp Đồng Lao Động', white)
        sheet.merge_range('U4:W4', 'Thông tin chi tiết về CMTND', white)
        sheet.merge_range('X4:AE4', 'Thông tin cá nhân', white)
        sheet.merge_range('AF4:AL4', 'Mức lương', white)
        sheet.write(3,40, 'Thông tin Ngân Hàng', white)
        sheet.merge_range('AP4:AQ4', 'Giảm trừ gia cảnh', white)
        sheet.merge_range('AR4:AX4', '', white)
        sheet.merge_range('AY4:BK4', 'Thông tin Hợp Đồng Lao Động', white)

        sheet.merge_range('BL4:BQ4', 'Đánh giá kết quả công việc', white)
        sheet.write(3,69, ' thông tinh BHXH', white)
        sheet.merge_range('BS4:BU4', 'Thông tin BHYT', white)

        # line 5
        sheet.merge_range('D5:E5', '',)
        sheet.merge_range('AP5', '',)
        sheet.merge_range('F5:G5', '',)
        sheet.merge_range('H5:I5', '',)
        sheet.merge_range('J5:K5', '',)
        sheet.merge_range('M5:P5', '',)
        sheet.merge_range('AI5:AJ5', '',)
        sheet.merge_range('AU5:BA5', '',)
        sheet.merge_range('BB5:BE5', '',)
        sheet.merge_range('BF5:BI5', '',)
        sheet.merge_range('BJ5:BK5', '',)

        sheet.merge_range('BO5', '',violet)
        sheet.merge_range('BP5', '',violet)
        sheet.merge_range('BQ5', '',violet)
        sheet.merge_range('BR5', '',violet)
        sheet.merge_range('BS5', '',violet)
        sheet.merge_range('BT5', '',violet)

        # line 6
        sheet.merge_range('BO6', '',violet)
        sheet.merge_range('BP6', '',violet)
        sheet.merge_range('BQ6', '',violet)
        sheet.merge_range('BR6', '',violet)
        sheet.merge_range('BS6', '',violet)
        sheet.merge_range('BT6', '',violet)
        sheet.write_row(4, 0, sheet_title_eng, title_style)
        sheet.write_row(5, 0, sheet_title, title_style)
        
        # set hight row
        sheet.set_row(4,55)
        sheet.set_row(5,50)
        sheet.freeze_panes(6, 1)
        row = 6
        seq=1
        for rec in list_employee:
            col = 0
            sheet.write(row, col, str(seq)) #_("STT")
            col +=1
            sheet.write(row, col, str(rec.barcode)) #_("MSNV"),
            col +=1
            sheet.write(row, col, rec.name.upper()) #_("Họ và tên viết in"),
            col +=1
            sheet.write(row, col, rec.title_id.name if rec.title_id else rec.job_id.name) #_("chức danh"),
            col +=1
            sheet.write(row, col, rec.job_id.name) #_("Position"),
            col +=1
            sheet.write(row, col, self.get_translate_value(rec.department_id)) # _("Phòng ban"),
            col +=1
            sheet.write(row, col, rec.department_id.name) #_("Dept."),
            col +=1
            sheet.write(row, col, rec.barcode or "") #_("Code"),
            col +=1
            sheet.write(row, col, rec.address_id.name) #_("Nơi làm việc."),
            col +=1
            sheet.write(row, col, rec.contract_id.date_start,date_format) # _("Ngày bắt đầu"),
            col +=1
            sheet.write(row, col, rec.contract_id.date_end,date_format)  #_("Ngày kết thúc"),
            col +=1
            sheet.write(row, col, self.get_resignation_reason(rec)) #_("Lý do nghỉ việc"),
            col +=1
            sheet.write(row, col, rec.contract_id.date_start,date_format)  #_("HĐLĐ từ"),
            col +=1
            sheet.write(row, col, rec.contract_id.date_end,date_format)   #__("HĐLĐ đến"),
            col +=1
            sheet.write(row, col, rec.contract_id.contract_type_id.name)  #__("Loại HĐ"),
            col +=1
            sheet.write(row, col, rec.contract_id.name)  #_("Mã HĐ"),
            col +=1
            sheet.write(row, col, '')  #_("Số nội bộ"),
            col +=1
            sheet.write(row, col, rec.work_phone)  #_("Điện thoại di động"),
            col +=1
            sheet.write(row, col, rec.work_email)  # _("Địa chỉ email"),
            col +=1
            sheet.write(row, col, rec.phone)  # _("mail ca nhan"),
            col +=1
            sheet.write(row, col, rec.identification_id)  #_("Số CMTND"),
            col +=1
            sheet.write(row, col, rec.identification_created_date,date_format)  #_("Ngày cấp"),
            col +=1
            sheet.write(row, col, rec.identification_created_place,date_format)  #_("Nơi cấp"),
            col +=1
            sheet.write(row, col, rec.birthday,date_format)  #_("Ngày tháng năm sinh"),
            col +=1
            sheet.write(row, col, rec.place_of_birth)  #_("Nơi sinh"),
            col +=1
            sheet.write(row, col, rec.gender)  #_("Giới tính"),
            col +=1
            sheet.write(row, col, rec.ethnic)  #_("Dân tộc"),
            col +=1
            sheet.write(row, col, rec.place_of_birth)  #_("Nguyên quán"),
            col +=1
            sheet.write(row, col, rec.certificate)  #_("Trình độ học vấn"),
            col +=1
            sheet.write(row, col, rec.place_of_permanent)  #_("Địa chỉ thường trú"),
            col +=1
            sheet.write(row, col, rec.place_of_permanent)  # _("Địa chỉ Liên lạc"),
            col +=1
            sheet.write(row, col, rec.contract_id.wage if rec.contract_id.contract_type_id.is_trial else '',format_currency)  #_("Lương thử việc"),
            col +=1
            sheet.write(row, col, rec.contract_id.allowance_ids.amount)  #_("Phụ cấp trách nhiệm"),
            col +=1
            sheet.write(row, col, '? Luong 2016')  #_("Lương 2016"),
            col +=1
            sheet.write(row, col, rec.contract_id.wage,format_currency)  #_("Lương sau thử việc"),
            col +=1 
            sheet.write(row, col, rec.contract_id.wage,format_currency)  #_("Lương căn bản"),
            col +=1  
            sheet.write(row, col, '')  #_("Thưởng hoàn thành công việc"),
            col +=1  
            sheet.write(row, col, rec.contract_id.allowance_ids.amount)  #_("Phụ cấp trách nhiệm"),
            col +=1  
            sheet.write(row, col, '')  #__("KCBBĐ"),
            col +=1  
            sheet.write(row, col, rec.study_field)  #_("Trình độ chuyên môn"),
            col +=1  
            sheet.write(row, col, rec.bank_account_id.acc_number)  # _("Số TK"),
            col +=1  
            sheet.write(row, col, rec.tax_code)  # _("Mã số thuế"),
            col +=1  
            sheet.write(row, col, rec.number_of_dependent)  #__("Số người phụ thuộc"),
            col +=1  
            sheet.write(row, col, '')  #_("Thời gian gia nhập công đoàn"),
            col +=1  
            sheet.write(row, col, '')  #_("Họ tên con"),
            col +=1  
            sheet.write(row, col, '',date_format)  #_("Ngày tháng năm sinh"),,
            col +=1  
            sheet.write(row, col, '')  #_("Họ tên con"),
            col +=1  
            sheet.write(row, col, '',date_format)  #_("Ngày tháng năm sinh"),,
            col +=1  
            sheet.write(row, col, '')  #_("Họ tên con"),
            col +=1  
            sheet.write(row, col, '',date_format)  #_("Ngày tháng năm sinh"),
            col +=1  

            sheet.write(row, col, rec.contract_id.date_start,date_format)  #_("HĐLĐ lần 1 từ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.date_end,date_format)  # _("HĐLĐ lần 1 đến"),
            col +=1  
            sheet.write(row, col, rec.contract_id.contract_type_id.name)  #_("Loại HĐ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.name)  #_("Mã HĐ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.date_start,date_format)  #_("HĐLĐ lần 2 từ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.date_end,date_format)  #_("HĐLĐ lần 2 đến"),
            col +=1  
            sheet.write(row, col, rec.contract_id.contract_type_id.name)  #_("Loại HĐ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.name)  #_("Mã HĐ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.date_start,date_format)  #_("HĐLĐ lần 3 từ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.date_end,date_format)  #_("số thứ tự HĐ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.contract_type_id.name)  #_("Loại HĐ"),
            col +=1  
            sheet.write(row, col, rec.contract_id.name)  #_("Mã HĐ"),
            col +=1  
            sheet.write(row, col, '')  #_("Số tháng làm việc"),
            col +=1  
            sheet.write(row, col, '')  #__("Nhân viên (Mẫu KPI, 1 lần/tháng) VND"),
            col +=1  
            sheet.write(row, col, '')  #_("Nhân viên (Mẫu KPI, 1 lần/tháng) USD"),
            col +=1  
            sheet.write(row, col, '')  #_("Quản lý (mẫu PMP 1 lần/năm) VND"),
            col +=1 
            sheet.write(row, col, '')  #_("Quản lý (mẫu PMP 1 lần/năm) USD"),
            col +=1   
            sheet.write(row, col, '')  #_("Đào tạo (Mẫu Trainer, 2 lần/năm) VND"),
            col +=1   
            sheet.write(row, col, '')  # _("Đào tạo (Mẫu Trainer, 2 lần/năm) USD"),
            col +=1   
            sheet.write(row, col, rec.social_insurance_no)  # _("Số sổ BHXH"),
            col +=1   
            sheet.write(row, col, '')  #_("Nơi đăng ký KCB"),
            col +=1   
            sheet.write(row, col, rec.health_insurance_no)  #_("Số thẻ KCB"),
            col +=1      
            sheet.write(row, col,'')  #_("Ngày tham gia BHXH, YT, TN"),
            row+=1
            seq+=1