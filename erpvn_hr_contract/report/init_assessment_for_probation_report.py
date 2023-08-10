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
from openerp.addons.init_utils.utils.amount_to_text_vi import amount_to_text_vi
from openerp.addons.init_utils.utils.amount_to_text_en import amount_to_text_en


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_report': self._get_report,
            'change_date_format': self.change_date_format,
        })
        self.context = context

    def change_date_format(self, date):
        date = datetime_utils.str_to_date(date)
        return {
            'date': self.formatLang(date, date=True),
        }

    def _get_report(self, context=None):
        if context is None:
            context = {}
        employee_obj = self.pool.get('hr.employee')
        res = []
        for line in employee_obj.browse(self.cr, self.uid, self.ids, context=context):
            res.append({
                'employee_name': line.name,
                'staff_code': line.internal_code,
                'department': line.department_id and u'{}/{}'.format(line.department_id.name_vn or '', line.department_id.name) or '',
                'job': line.job_id and u'{}/{}'.format(line.job_id.name_vn or '', line.job_id.name) or '',
                'start_probation': line.main_contract_id and self.change_date_format(line.main_contract_id.date_start) or '',
                'end_probation': line.main_contract_id and self.change_date_format(line.main_contract_id.date_end) or '',
            })
        return res

