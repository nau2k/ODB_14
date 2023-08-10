# -*- coding: utf-8 -*-
######################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2011 OpenERP s.a. (<http://openerp.com>).
# Copyright (C) 2013 INIT Tech Co., Ltd (http://init.vn).
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
######################################################################



from openerp.addons.init_utils.utils import datetime_utils
from datetime import datetime
from openerp.report import report_sxw
from openerp.tools.translate import _


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_data': self._get_data,
        })

    def _get_data(self, datas):
        employee_obj = self.pool.get('hr.employee')
        contract_obj = self.pool.get('hr.contract')
        emp_ids = datas.get('emp_ids', [])
        res = []
        for emp in employee_obj.browse(self.cr, self.uid, emp_ids):
            contract_ids = contract_obj.search(self.cr, self.uid,
                                               [('contract_ref_id', '=', emp.main_contract_id.id)], order='id desc')
            emp_contract = contract_obj.browse(self.cr, self.uid, contract_ids)[0]
            res.append({
                'emp_code': emp.internal_code or '',
                'emp_name': emp.name,
                'emp_birthday': emp.birthday or '',
                'emp_dept': emp.department_id and emp.department_id.name or '',
                'emp_pos': emp.job_id and emp.job_id.name or '',
                'signed_contract_date': datas['signed_contract_date'] and self.formatLang(datas['signed_contract_date'], date=True) or '',
                'contract_type': datas['contract_type'],
                'evaluation_end_from': datas['evaluation_end_from'] and self.formatLang(datas['evaluation_end_from'], date=True) or '',
                'evaluation_end_to': datas['evaluation_end_to'] and self.formatLang(datas['evaluation_end_to'], date=True) or '',
                'return_date': datas['return_date'] and self.formatLang(datas['return_date'], date=True) or '',
                'start_date_contract':  emp_contract and self.formatLang(emp_contract.date_start, date=True) or '',
                'wage':  emp_contract and self.formatLang(emp_contract.wage, dp='Currency') or 0,
            })
        return res




