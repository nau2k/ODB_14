# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FormulaModel(models.Model):
    _name = "formula.model"
    _description = "Formula Model"

    name = fields.Char(string="Name", required=True, translate=True)
    formula = fields.Text(string='Formula',
        default='''
# Formula:
#----------------------
# length: length of object
# width: width of object
# height: height of object
# od: outside diameter of object
# id: inside diameter of object
# rate: rate of object
# area: area of object
# perimeter: perimeter of object
# operators: + - * /
# floating point: .

1/2 * (length + area * (perimeter / 3.2)) * (width + height)''')