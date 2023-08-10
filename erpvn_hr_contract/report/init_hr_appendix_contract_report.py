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
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_day': self.get_day,
            'change_date_format': self.change_date_format,
            'upper': self.upper,
            'today': self.today,
            'total': self.total,
            'get_parameter_group': self.get_parameter_group,
        })
        self.context = context

    def get_day(self, date):
        date = datetime_utils.str_to_date(date)
        return {
            'day': date.strftime("%d"),
            'month': date.strftime("%m"),
            'year': date.strftime("%Y"),
        }

    def change_date_format(self, date):
        date = datetime_utils.str_to_date(date)
        return {
            'date': self.formatLang(date, date=True),
        }

    def upper(self, string):
        return string.upper()

    def today(self):
        return datetime.today()

    def total(self, val1, val2):
        return float(val1+val2)

    def get_parameter_group(self, parameter_group_id):
        res = []
        if parameter_group_id:
            para = self.pool.get("hr.payslip.parameter.group").browse(self.cr, self.uid, parameter_group_id)
            for line in para.line_ids:
                alw_name = line.allowance_id.name.split('/')
                name = alw_name[1] if len(alw_name) > 1 else alw_name[0]

                res.append({
                    'name': u'Phụ cấp %s' % name or '',
                    'value': line.value or '',
                })
        return res