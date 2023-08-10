# -*- coding: utf-8 -*-
from odoo import models
import string
from dateutil.relativedelta import relativedelta
from odoo.addons.erpvn_hr_payroll.models.hr_payslip import HOLIDAY_CODES


class PayrollReport(models.AbstractModel):
    _name = 'report.xlsx_payroll_report.xlsx_payroll_report' 
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Xlsx Payroll Report'

    def _set_title_columns(self, workbook, sheet):
        allowance_merge_format = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#ffff99', 'border': 1, 'border_color': '#ffffff'})
        overtime_merge_format = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#993300', 'border': 1, 'border_color': '#ffffff'})
        insurance_merge_format = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#ff8080', 'border': 1, 'border_color': '#ffffff'})
        deduction_merge_format = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#c0c0c0', 'border': 1, 'border_color': '#ffffff'})
        tax_merge_format = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#ffcc99', 'border': 1, 'border_color': '#ffffff'})
        res_merge_format = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#5eb91e', 'border': 1, 'border_color': '#ffffff'})

        # Create a format to use in the merged range.user.employee_id
        merge_format1 = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#33cccc', 'border': 1, 'border_color': '#ffffff'})
        merge_format2 = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#ff6600', 'border': 1, 'border_color': '#ffffff'})
        merge_format3 = workbook.add_format({'font_name': 'Times New Roman', 'bold': 1, 
            'align': 'center', 'valign': 'vcenter', 'bg_color': '#3366ff', 'border': 1, 'border_color': '#ffffff'})
        # List report column headers:
        sheet.merge_range('A5:A9', 'NO/STT', merge_format1)
        sheet.set_column('B:B', 10)
        sheet.merge_range('B5:B9', 'Employee\nCode/MSNV', merge_format1)
        sheet.set_column('C:C', 20)
        sheet.merge_range('C5:C9', 'Employee Name\nHọ & Tên', merge_format1)
        sheet.set_column('D:D', 14)
        sheet.merge_range('D5:D9', 'Vietnamese (V)\nExpat (E)', merge_format1)
        sheet.set_column('E:E', 20)
        sheet.merge_range('E5:E9', 'Department\nPhòng Ban', merge_format1)
        sheet.set_column('F:F', 16)
        sheet.merge_range('F5:F9', 'Position\nChức danh', merge_format1)
        sheet.set_column('G:G', 16)
        sheet.merge_range('G5:G9', 'Employee Status\nLoại NV', merge_format1)

        # BASIC
        sheet.set_column('H:K', 20)

        sheet.merge_range('H5:H8', 'Gross Salary\nLương Thỏa Thuận', merge_format2)
        sheet.write('H9', 'VND', merge_format2)

        basics_dict = {
            'I': ['Expected Working Hours\nGiờ Làm Việc Dự Kiến', ''],
            'J': ['Actual Working Hours\nGiờ Làm Việc Thực Tế', ''],
            'K': ['Actual Salary\nLương Thực Tế', 'VND'],
        }
        for k, v in basics_dict.items():
            range_str = '%(col)s5:%(col)s8' % {'col': k}
            currency_str = '%s9' % k

            sheet.merge_range(range_str, v[0], merge_format3)
            sheet.write(currency_str, v[1], merge_format3)


        # ALLOWANCES
        sheet.set_column('L:AA', 16)
        sheet.merge_range('L5:AA6', 'Allowance\nPhụ Cấp', allowance_merge_format)

        allowances_dict = {
            'L': 'Attendance\nKỷ Luật',
            'M': 'Hazardous\nĐộc Hại',
            'N': 'Handphone\nĐiện Thoaị',
            'O': 'Fuel\nXăng Dầu',
            'P': 'Skill\nTrách Nhiệm/Tay Nghề',
            'Q': 'Artifacts\nPhụ cấp hiện vật',
            'R': 'Transportation\nĐi lại',
            'S': 'Caterring\nCơm Tăng Ca',
            'T': 'Responsibility\nPhụ cấp trách nhiệm',
            'U': 'House Rental\nTiền thuê nhà',
            'V': 'KPI\nThưởng hiệu suất	',
            'W': 'Lương thưởng\ntháng 13',
            'X': 'Annual Leave',
            'Y': 'Other\nKhác',
            'Z': 'Total Allowance\nTổng phụ cấp\n+ Thưởng (Tính thuế)',	
            'AA': 'Allowance\n(Non Taxable)\nPhụ cấp\n(Không tính thuế)',
        }
        sheet.set_row(4, 16)
        sheet.set_row(5, 16)
        sheet.set_row(6, 30)
        sheet.set_row(7, 30)
        sheet.set_row(8, 16)
        for k, cont_str in allowances_dict.items():
            range_str = '%(col)s7:%(col)s8' % {'col': k}
            currency_str = '%s9' % k

            sheet.merge_range(range_str, cont_str, allowance_merge_format)
            sheet.write(currency_str, 'VND', allowance_merge_format)

        # OVERTIME
        sheet.set_column('AB5:AT6', 16)
        sheet.merge_range('AB5:AT6', 'Overtime\nTăng ca', overtime_merge_format)
        overtime_dict = {
            'AB': ['2.0', 'Hours'],
            'AC': ['2.7', 'Hours'],
            'AD': ['2.1', 'Hours'],
            'AE': ['1.5', 'Hours'],
            'AF': ['1.3', 'Hours'],
            'AG': ['1.0', 'Hours'],
            'AH': ['Taxable\nTính thuế 2.0', 'VND'],
            'AI': ['Non Taxable\nKhông tính thuế 2.0', 'VND'],
            'AJ': ['Taxable\nTính thuế 2.7', 'VND'],
            'AK': ['Non Taxable\nKhông tính thuế 2.7', 'VND'],
            'AL': ['Taxable\nTính thuế 2.1', 'VND'],
            'AM': ['Non Taxable\nKhông tính thuế 2.1', 'VND'],
            'AN': ['Taxable\nTính thuế 1.5', 'VND'],
            'AO': ['Non Taxable\nKhông tính thuế 1.5', 'VND'],
            'AP': ['Taxable\nTính thuế 1.3', 'VND'],
            'AQ': ['Non Taxable\nKhông tính thuế 1.3', 'VND'],
            'AR': ['Taxable\nTính thuế 1.0', 'VND'],
            'AS': ['Non Taxable\nKhông tính thuế 1.0', 'VND'],
            'AT': ['Total of OT\nTổng tăng ca', 'VND'],
        }

        for k, v in overtime_dict.items():
            range_str = '%(col)s7:%(col)s8' % {'col': k}
            currency_str = '%s9' % k

            sheet.merge_range(range_str, v[0], overtime_merge_format)
            sheet.write(currency_str, v[1], overtime_merge_format)

        # insurances
        sheet.merge_range('AU5:BD5', 'Compulsory / Bảo hiểm', insurance_merge_format)

        sheet.merge_range('AU6:AY6', 'Employee Contribution / Người Lao Động Trả', insurance_merge_format)
        sheet.merge_range('AZ6:BD6', 'Company Contribution / Công Ty Trả', insurance_merge_format)

        insurances_dict = {
            'AU': ['SI', '8%'],
            'AV': ['HI', '1.5%'],
            'AW': ['UI', '1%\n0% (expat)'],
            'AX': ['TU', '60,000'],
            'AZ': ['SI', '17.5%'],
            'BA': ['HI', '3%'],
            'BB': ['UI', '1%\n0% (expat)'],
            'BC': ['TU', '2%'],
        }
        for k, val in insurances_dict.items():
            col_str1 = '%s7' % k
            col_str2 = '%s8' % k
            col_str3 = '%s9' % k

            sheet.write(col_str1, val[0], insurance_merge_format)
            sheet.write(col_str2, val[1], insurance_merge_format)
            sheet.write(col_str3, 'VND', insurance_merge_format)

        sheet.merge_range('AY7:AY8', 'Total\nInsurance', insurance_merge_format)
        sheet.write('AY9', 'VND', insurance_merge_format)
        sheet.merge_range('BD7:BD8', 'Total\nInsurance', insurance_merge_format)
        sheet.write('BD9', 'VND', insurance_merge_format)

        # deduction
        sheet.merge_range('BE5:BH5', 'Tax Deduction / Giảm trừ thuế', deduction_merge_format)
        sheet.set_column('BE:BH', 16)
        deductions_dict = {
            'BE': ['Tax payer\nGiảm trừ bản thân\n\n11,000,000', 'VND'],
            'BF': ['No of dependants\nSố người phụ thuộc', ''],
            'BG': ['Dependent deduction\nGiảm trừ phụ thuộc\n\n4,400,000', 'VND'],
            'BH': ['Total Tax deduction\nTổng giảm trừ thuế', 'VND'],
        }

        for k, val in deductions_dict.items():
            col_str1 = '%(col)s6:%(col)s8' % {'col': k}
            col_str2 = '%s9' % k
            sheet.merge_range(col_str1, val[0], deduction_merge_format)
            sheet.write(col_str2, val[1], deduction_merge_format)

        # tax
        sheet.merge_range('BI5:BK6', 'Personal Income Tax\nThuế TNCN', tax_merge_format)
        sheet.set_column('BI:BK', 16)
        taxes_dict = {
            'BI': ['Taxable Income\nThu nhập chịu thuế', 'VND'],
            'BJ': ['Assessable Income\nThu nhập tính thuế', 'VND'],
            'BK': ['PIT\nTNCN', 'VND'],
        }

        for k, val in taxes_dict.items():
            col_str1 = '%(col)s7:%(col)s8' % {'col': k}
            col_str2 = '%s9' % k
            sheet.merge_range(col_str1, val[0], tax_merge_format)
            sheet.write(col_str2, val[1], tax_merge_format)

        # res
        sheet.set_column('BL:BO', 16)
        res_dict = {
            'BL': ['Advance\nTạm ứng', 'VND'],
            'BM': ['Net take from\nhome salary\nThực nhận', 'VND'],
            'BN': ['Total Company Cost\nTổng Chi Phí\nCông Ty', 'VND'],
            'BO': ['Bank Account\nSố TK NH', ''],
        }

        for k, val in res_dict.items():
            col_str1 = '%(col)s5:%(col)s8' % {'col': k}
            col_str2 = '%s9' % k
            sheet.merge_range(col_str1, val[0], res_merge_format)
            sheet.write(col_str2, val[1], res_merge_format)

    def _set_allowances_data(self, slip, dept_row, currency_format, sheet):
        sheet.write('L' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'attendance').mapped('total')), 0), currency_format)
        sheet.write('M' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'hazardous').mapped('total')), 0), currency_format)
        sheet.write('N' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'phone').mapped('total')), 0), currency_format)
        sheet.write('O' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'fuel').mapped('total')), 0), currency_format)
        sheet.write('P' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'skill').mapped('total')), 0), currency_format)
        sheet.write('Q' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'artifact').mapped('total')), 0), currency_format)
        sheet.write('R' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'transport').mapped('total')), 0), currency_format)
        sheet.write('S' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'meal').mapped('total')), 0), currency_format)
        sheet.write('T' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'respon').mapped('total')), 0), currency_format)
        sheet.write('U' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'house_rental').mapped('total')), 0), currency_format)
        sheet.write('V' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'kpi_oee').mapped('total')), 0), currency_format)
        sheet.write('W' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'th13_salary').mapped('total')), 0), currency_format)
        sheet.write('X' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'annual_leave_2016').mapped('total')), 0), currency_format)
        sheet.write('Y' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'other_allowance').mapped('total')), 0), currency_format)
        sheet.write('Z' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'TotalAlw').mapped('total')), 0), currency_format)
        sheet.write('AA' + str(dept_row), round(sum(slip.line_ids.filtered(lambda x: x.code == 'NonTaxBonusTotal').mapped('total')), 0), currency_format)

    def _set_ot_hours(self, slip, dept_row, float_num_format, sheet):
        sheet.write('AB' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'WkOTHours').mapped('total')), float_num_format)
        sheet.write('AC' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'NightWkOTHours').mapped('total')), float_num_format)
        sheet.write('AD' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'NightReOTHours').mapped('total')), float_num_format)
        sheet.write('AE' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTHours').mapped('total')), float_num_format)
        sheet.write('AF' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTHours13').mapped('total')), float_num_format)
        sheet.write('AG' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTHours10').mapped('total')), float_num_format)

    def _set_ot_costs(self, slip, dept_row, currency_format, sheet):
        sheet.write('AH' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'WeekOTSalTax').mapped('total')), currency_format)
        sheet.write('AI' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'WeekOTSalNonTax').mapped('total')), currency_format)
        sheet.write('AJ' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'NightWeekOTSalTax').mapped('total')), currency_format)
        sheet.write('AK' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'NightWeekOTSalNonTax').mapped('total')), currency_format)
        sheet.write('AL' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'NightReOTSalTax').mapped('total')), currency_format)
        sheet.write('AM' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'NightReOTSalNonTax').mapped('total')), currency_format)
        sheet.write('AN' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTSalTax').mapped('total')), currency_format)
        sheet.write('AO' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTSalNonTax').mapped('total')), currency_format)
        sheet.write('AP' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTSalTax13').mapped('total')), currency_format)
        sheet.write('AQ' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTSalNonTax13').mapped('total')), currency_format)
        sheet.write('AR' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTSalTax10').mapped('total')), currency_format)
        sheet.write('AS' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'ReOTSalNonTax10').mapped('total')), currency_format)
        sheet.write('AT' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'OTTotal').mapped('total')), currency_format)

    def _set_insurance_costs(self, slip, dept_row, currency_format, use_filter, view_type, view_id, sheet):
        SocInsL_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'SocInsL').mapped('total'))
        HealthInsL_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'HealthInsL').mapped('total'))
        UnempInsL_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'UnempInsL').mapped('total'))
        UnionFee_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'UnionFee').mapped('total'))
        EmpSocSec_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'EmpSocSec').mapped('total'))
        CompSocInsL_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'CompSocInsL').mapped('total'))
        CompHealthInsL_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'CompHealthInsL').mapped('total'))
        CompUnempInsL_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'CompUnempInsL').mapped('total'))
        UnionFeeCom_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'UnionFeeCom').mapped('total'))
        CompEmpSocSec_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'CompSocSec').mapped('total'))

        if use_filter:
            SocInsL_amount = slip.line_ids.filtered(lambda x: x.code == 'SocInsL' and getattr(x, '%s_id' % view_type) == view_id).total
            HealthInsL_amount = slip.line_ids.filtered(lambda x: x.code == 'HealthInsL' and getattr(x, '%s_id' % view_type) == view_id).total
            UnempInsL_amount = slip.line_ids.filtered(lambda x: x.code == 'UnempInsL' and getattr(x, '%s_id' % view_type) == view_id).total
            UnionFee_amount = slip.line_ids.filtered(lambda x: x.code == 'UnionFee' and getattr(x, '%s_id' % view_type) == view_id).total
            EmpSocSec_amount = slip.line_ids.filtered(lambda x: x.code == 'EmpSocSec' and getattr(x, '%s_id' % view_type) == view_id).total
            CompSocInsL_amount = slip.line_ids.filtered(lambda x: x.code == 'CompSocInsL' and getattr(x, '%s_id' % view_type) == view_id).total
            CompHealthInsL_amount = slip.line_ids.filtered(lambda x: x.code == 'CompHealthInsL' and getattr(x, '%s_id' % view_type) == view_id).total
            CompUnempInsL_amount = slip.line_ids.filtered(lambda x: x.code == 'CompUnempInsL' and getattr(x, '%s_id' % view_type) == view_id).total
            UnionFeeCom_amount = slip.line_ids.filtered(lambda x: x.code == 'UnionFeeCom' and getattr(x, '%s_id' % view_type) == view_id).total
            CompEmpSocSec_amount = slip.line_ids.filtered(lambda x: x.code == 'CompSocSec' and getattr(x, '%s_id' % view_type) == view_id).total

        sheet.write('AU' + str(dept_row), round(SocInsL_amount, 0), currency_format)
        sheet.write('AV' + str(dept_row), round(HealthInsL_amount, 0), currency_format)
        sheet.write('AW' + str(dept_row), round(UnempInsL_amount, 0), currency_format)
        sheet.write('AX' + str(dept_row), round(UnionFee_amount, 0), currency_format)
        sheet.write('AY' + str(dept_row), round(EmpSocSec_amount, 0), currency_format)
        sheet.write('AZ' + str(dept_row), round(CompSocInsL_amount, 0), currency_format)
        sheet.write('BA' + str(dept_row), round(CompHealthInsL_amount, 0), currency_format)
        sheet.write('BB' + str(dept_row), round(CompUnempInsL_amount, 0), currency_format)
        sheet.write('BC' + str(dept_row), round(UnionFeeCom_amount, 0), currency_format)
        sheet.write('BD' + str(dept_row), round(CompEmpSocSec_amount, 0), currency_format)

        # Deduction
        sheet.write('BE' + str(dept_row), slip.line_ids.filtered(lambda x: x.code == 'DedTaxP')[-1].total, currency_format)
        sheet.write('BF' + str(dept_row), slip.line_ids.filtered(lambda x: x.code == 'NbDep')[-1].total, currency_format)
        sheet.write('BG' + str(dept_row), slip.line_ids.filtered(lambda x: x.code == 'DedDep')[-1].total, currency_format)
        TotalTaxDed_amount = slip.line_ids.filtered(lambda x: x.code == 'TotalTaxDed')[-1].total
        sheet.write('BH' + str(dept_row), round(TotalTaxDed_amount, 0), currency_format)

        # Tax Income, Assessable Income, PIT
        TaxInc_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'TaxInc').mapped('total'))
        sheet.write('BI' + str(dept_row), round(TaxInc_amount, 0), currency_format)
        AsseInc_amount = max(TaxInc_amount - EmpSocSec_amount - TotalTaxDed_amount, 0)
        sheet.write('BJ' + str(dept_row), round(AsseInc_amount, 0), currency_format)
        PIT_amount = round(max(0, AsseInc_amount <= 5000000 and AsseInc_amount * 0.05 or AsseInc_amount <= 10000000 and AsseInc_amount * 0.1 - 250000  or \
            AsseInc_amount <= 18000000 and AsseInc_amount * 0.15 - 750000 or AsseInc_amount <= 32000000 and AsseInc_amount * 0.2 - 1650000 or \
            AsseInc_amount <= 52000000 and AsseInc_amount * 0.25 - 3250000  or AsseInc_amount <= 80000000 and AsseInc_amount * 0.3 - 5850000 or \
            AsseInc_amount > 80000000 and AsseInc_amount * 0.35 - 9850000), 0)

        if view_type == 'contract' and view_id.is_trial and (slip.employee_id.employee_type_id.name == 'Office' or \
                not slip.employee_id.tax_code) and TaxInc_amount >= 2000000:

            PIT_amount = TaxInc_amount * 0.1

        sheet.write('BK' + str(dept_row), round(PIT_amount, 0), currency_format)

        reimbursement_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'reimbursement').mapped('total'))
        sheet.write('BL' + str(dept_row), round(reimbursement_amount, 0), currency_format)

        GrossSal_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'GrossSal').mapped('total'))
        NonTaxBonusTotal_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'NonTaxBonusTotal').mapped('total'))
        advanced_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'advanced').mapped('total'))

        NetInc_amount = GrossSal_amount - PIT_amount + advanced_amount - reimbursement_amount - EmpSocSec_amount + NonTaxBonusTotal_amount - UnionFee_amount
        sheet.write('BM' + str(dept_row), round(max(NetInc_amount, 0), -3), currency_format)
        sheet.write('BN' + str(dept_row), round(GrossSal_amount + CompEmpSocSec_amount + UnionFeeCom_amount, -3), currency_format)

    def generate_xlsx_report(self, workbook, data, lines):
        format4 = workbook.add_format({'font_size':12, 'align': 'vcenter', 'bold': True})
        format5 = workbook.add_format({'font_size':12, 'align': 'vcenter', 'bold': False})

        # Generate Workbook
        sheet = workbook.add_worksheet('Payroll')

        #Report Details:
        for slip in lines.slip_ids:
            batch_period = str(slip.date_from.strftime('%B %d, %Y')) + '  To  ' + str(slip.date_to.strftime('%B %d, %Y'))
            company_name = slip.company_id.name
            break
    
        # Company Name
        sheet.write(0,0,company_name,format4)
        sheet.write(0,2,'Payslip Period:',format4)
        sheet.write(0,3,batch_period,format5)
    

        self._set_title_columns(workbook, sheet)

        department_format = workbook.add_format({'font_name': 'Arial', 'bold': 1, 
            'align': 'left', 'valign': 'vcenter', 'bg_color': '#ffffcc', 'border': 1, 'border_color': '#000000'})

        currency_format = workbook.add_format({'font_name': 'Arial', 'align': 'vcenter', 'bold': False, 'num_format': '#,##0'})
        float_num_format = workbook.add_format({'font_name': 'Arial', 'align': 'vcenter', 'bold': False, 'num_format': '##0.00'})

        dept_row = 11
        slip_row = 1
        for department_id in lines.mapped('slip_ids.employee_id.department_id'):
        # for department_id in lines.mapped('slip_ids.department_id'):
            sheet.merge_range('A' + str(dept_row) + ':BO' + str(dept_row), department_id.name, department_format)
            dept_row += 1
            
            # for slip in lines.slip_ids.filtered(lambda x: x.department_id.id == department_id.id):
            for slip in lines.slip_ids.filtered(lambda x: x.employee_id.department_id.id == department_id.id):
                sheet.write('A' + str(dept_row), str(slip_row))
                sheet.write('B' + str(dept_row), str(slip.employee_id.barcode))
                sheet.write('C' + str(dept_row), str(slip.employee_id.name))
                sheet.write('D' + str(dept_row), 'V' if slip.struct_id.code != 'OFFICER_SALARY_EXPAT' else 'E')
                sheet.write('E' + str(dept_row), str(slip.employee_id.department_id.name or ''))
                sheet.write('F' + str(dept_row), str(slip.employee_id.title_id.name or ''))

                force_ins, emp_type = True, 'Full'
                if slip.worked_days_line_ids.mapped('contract_id'):
                    force_ins = slip.worked_days_line_ids.mapped('contract_id')[-1].force_ins

                    # insurance computed on subcontract.
                    if not force_ins and slip.worked_days_line_ids.mapped('subcontract_id'):
                        force_ins = slip.worked_days_line_ids.mapped('subcontract_id')[-1].force_ins

                if not force_ins:
                    emp_type = 'Probation'

                if not slip.line_ids:
                    cols = list(string.ascii_uppercase) + \
                        ['AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM', 'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 'AW', 'AX', 'AY', 'AZ'] + \
                        ['BA', 'BB', 'BC', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BK', 'BL', 'BM', 'BN']

                    for i in cols[7:]:
                        sheet.write(i + str(dept_row), 0, currency_format)

                    sheet.write('BO' + str(dept_row), slip.employee_id.bank_account_id.acc_number if slip.employee_id.bank_account_id else '')

                    slip_row += 1
                    dept_row += 1
                    continue

                view_type = 'contract'
                view_id = False
                basic_lines = slip.line_ids.filtered(lambda x: x.code == 'BASIC')
                use_filter = False

                if len(basic_lines) == 1:
                    if basic_lines.contract_id:
                        view_id = basic_lines.contract_id
                    else:
                        view_type = 'subcontract'
                        view_id = basic_lines.subcontract_id
                else:
                    use_filter = True
                    temp = basic_lines[0]
                    view_type = 'contract' if temp.contract_id else 'subcontract'
                    view_id = temp.contract_id if temp.contract_id else temp.subcontract_id

                    # new way of get contract/subcontract to compute insurances
                    if slip.compute_ins_by != 'none':
                        view_type = slip.compute_ins_by
                        view_id = getattr(slip, slip.compute_ins_by + '_ins_id')
                    else:
                        # 2 contracts / 1 contract and 1 subcontract are trial.
                        cons = basic_lines.mapped('contract_id').filtered(lambda x: x.date_start <= (slip.date_to + relativedelta(day=15)))
                        if cons:
                            view_type = 'contract'
                            view_id = cons[-1]
                        else:
                            subcons = basic_lines.mapped('subcontract_id').filtered(lambda x: x.date_start <= (slip.date_to + relativedelta(day=15)))
                            if subcons:
                                view_type = 'subcontract'
                                view_id = subcons[-1]

                        # for basic_line in basic_lines[1:]:
                        #     if temp.total < basic_line.total:
                        #         temp = basic_line
                        #         view_type = 'contract' if temp.contract_id else 'subcontract'
                        #         view_id = temp.contract_id if temp.contract_id else temp.subcontract_id

                basic_amount = sum(slip.line_ids.filtered(lambda x: x.code == 'BASIC').mapped('total'))
                if use_filter:
                    contract_ids = basic_lines.mapped('contract_id')
                    if len(contract_ids) == len(basic_lines):
                        if contract_ids.filtered(lambda x: x.is_trial):
                            contract_id = contract_ids.filtered(lambda x: not x.is_trial)
                            if contract_id:
                                if contract_id.date_start <= (slip.date_to + relativedelta(day=15)):

                                    if emp_type == 'Probation':
                                        emp_type = 'Full'

                                    view_type = 'contract'
                                    view_id = contract_id

                    basic_amount = slip.line_ids.filtered(lambda x: x.code == 'BASIC' and getattr(x, '%s_id' % view_type) == view_id).total

                sheet.write('G' + str(dept_row), emp_type)
                sheet.write('H' + str(dept_row), basic_amount, currency_format)
                sheet.write('I' + str(dept_row), sum(slip.worked_days_line_ids.filtered(lambda x: x.code == 'ExWorkingDays').mapped('number_of_hours')), float_num_format)
                sheet.write('J' + str(dept_row), sum(slip.worked_days_line_ids.filtered(lambda x: x.code in HOLIDAY_CODES + ['WORK100', 'LATE100', 'BTPL', 'WFHL', 'MPPL', 'CU12PL', 'W28PL', 'ANPL', 'MRPL', 'MRRPL']).mapped('number_of_hours')), float_num_format)
                sheet.write('K' + str(dept_row), sum(slip.line_ids.filtered(lambda x: x.code == 'WorkingSal').mapped('total')), currency_format)

                self._set_allowances_data(slip, dept_row, currency_format, sheet)
                self._set_ot_hours(slip, dept_row, float_num_format, sheet)
                self._set_ot_costs(slip, dept_row, currency_format, sheet)
                self._set_insurance_costs(slip, dept_row, currency_format, use_filter, view_type, view_id, sheet)

                sheet.write('BO' + str(dept_row), slip.employee_id.bank_account_id.acc_number if slip.employee_id.bank_account_id else '')

                slip_row += 1
                dept_row += 1