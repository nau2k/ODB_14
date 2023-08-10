# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.tools import  float_utils, pycompat
import re


class FloatConverter(models.AbstractModel):
    _inherit = 'ir.qweb.field.float'

    @api.model
    def value_to_html(self, value, options):
        if 'decimal_precision' in options:
            precision = self.env['decimal.precision'].sudo().search([('name', '=', options['decimal_precision'])]).digits
        else:
            precision = options['precision']

        if precision is None:
            fmt = '%f'
        else:
            value = float_utils.float_round(value, precision_digits=precision)
            fmt = '%.{precision}f'.format(precision=precision)
        lang = self.user_lang()
        float_number = lang.format(fmt, value, grouping=True).replace(r'-', u'-\N{ZERO WIDTH NO-BREAK SPACE}')

        # %f does not strip trailing zeroes. %g does but its precision causes
        # it to switch to scientific notation starting at a million *and* to
        # strip decimals. So use %f and if no precision was specified manually
        # strip trailing 0.
        if precision is None:
            float_number = re.sub(r'(?:(0|\d+?)0+)$', r'\1', float_number)
        formatted_number = float_number.rstrip('0').rstrip('.') if lang.decimal_point in float_number else float_number

        return pycompat.to_text(formatted_number)