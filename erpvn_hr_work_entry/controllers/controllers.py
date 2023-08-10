# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, _
from odoo.http import request


class WorkEntryController(http.Controller):

    @http.route('/erpvn_hr_work_entry/timesheet_adjustment_request_line/view', type='http', auth="public")
    def view_timesheet_adjustment_request_line(self, id, **kwargs):
        action = request.env.ref("erpvn_hr_work_entry.my_timesheet_adjustment_request_line_action")
        return werkzeug.utils.redirect('/web#action=%s&model=timesheet.adjustment.request.line&id=%s&view_type=form' % (action.id, int(id)))
