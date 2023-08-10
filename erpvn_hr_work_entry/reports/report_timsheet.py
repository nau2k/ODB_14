# -*- coding: utf-8 -*-

import json

from odoo import api, models, _
from odoo.tools import float_round

class ReportTimeSheet(models.AbstractModel):
    _name = 'report.erpvn_hr_work_entry.report_timsheet'
    _description = 'Time Sheet Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name('erpvn_hr_work_entry.report_timsheet')
        docs = self.env[report.model].browse(docids)
        list_data = docs.browse(data['form'].get('data'))

        key_groups = {}
        for line in list_data:
            employee = line.employee_id
            if employee.name in key_groups:
                key_groups[employee.name][4].append(line.date_start)
                if line.work_entry_type_id in key_groups[employee.name][3][0]:
                    key_groups[employee.name][3][0][line.work_entry_type_id].append({line.date_start:[line.actual_duration]})
                else:
                    key_groups[employee.name][3][0][line.work_entry_type_id]=([{line.date_start:[line.actual_duration]}])
            else:
                 key_groups[employee.name]=[line.employee_id],[line.department_id],[{line.work_entry_type_id:[{line.date_start:[line.actual_duration]}]}],[line.date_start]
        datas = []
        list_date = []
        new_list = []

        for key,values in key_groups.items():
            datas.append(values)
            list_date.append(values[4])
        
        # xoa thoi gian khoi list
        for rec in datas:
            del_item=list(rec)
            del_item.pop(4)
            new_list.append(tuple((del_item)))
        
        # xu ly ngay trung lap
        date_convert=[]
        for rec in list_date[0]:
            date_convert.append(rec.date())
        date=list(set(date_convert))
        date.sort()
        return {
            'doc_ids': docids,
            'doc_model': 'hr.work.entry',
            'docs': docs,
            'data':new_list,
            'date':date
        }
