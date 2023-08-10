from odoo import api, fields, models, _,SUPERUSER_ID
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from lxml import etree
from odoo.osv import expression
from datetime import date
from datetime import datetime


class ResignApproved(models.TransientModel):
    _name = "wz.resign.approved"

    resign_confirm_ids = fields.Many2many(comodel_name='hr.resignation')
    expected_revealing_date = fields.Date(string="Last Day of Employee",
                                          help='Employee requested date on which he is revealing from the company.')
    resign_confirm_date = fields.Date(string="Confirmed Date",  default=fields.Date.today(),
                                      help='Date on which the request is confirmed by the employee.',
                                      track_visibility="always", )
    approved_revealing_date = fields.Date(string="Approved Last Day Of Employee",default=fields.Date.today(),
                                          help='Date on which the request is confirmed by the manager.',
                                          track_visibility="always")
    
    def action_ok(self):
        self.resign_confirm_ids._approve_resignation(self.approved_revealing_date)
                    
                    
                    
