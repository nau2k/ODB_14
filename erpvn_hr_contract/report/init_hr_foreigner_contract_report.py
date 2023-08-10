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
            'amount_to_text_vn': self.amount_to_text_vn,
            'amount_to_text_en': self.amount_to_text_en,
            'get_day': self.get_day,
            'change_date_format': self.change_date_format,
            'upper': self.upper,
            'get_selection_item': self.get_selection_item,
            'today': self.today,
        })
        self.context = context

    def capitalize(self, string):
        return string.capitalize()

    def upper(self, string):
        return string.upper()

    def amount_to_text_vn(self, amount):
        """

        :param amount:
        :return:
        """
        res = self.capitalize(amount_to_text_vi(amount, 'đồng/tháng'))
        return _(res)

    def amount_to_text_en(self, amount):
        """

        :param amount:
        :return:
        """
        return _(amount_to_text_en(amount, 'dong'))

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

    def get_selection_item(self, obj, field, value=None):
        try:
            if isinstance(obj, report_sxw.browse_record_list):
                obj = obj[0]
            if isinstance(obj, (str, unicode)):
                model = obj
                field_val = value
            else:
                model = obj._table_name
                field_val = getattr(obj, field)

            if field_val:
                return dict(
                        self.pool.get(model).fields_get(self.cr, self.uid, allfields=[field], context=self.context)[
                            field][
                            'selection'])[field_val]
            return ''
        except Exception:
            return ''

    def today(self):
        return datetime.today()
