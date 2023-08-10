# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, _
from odoo.http import request


class CalendarController(http.Controller):

    @http.route('/erpvn_hr_leave_management/holiday/view', type='http', auth="public")
    def view_holiday(self, id, **kwargs):
        action = request.env.ref("hr_holidays.hr_leave_action_action_approve_department")
        return werkzeug.utils.redirect('/web#action=%s&model=hr.leave&id=%s&view_type=form' % (action.id, int(id)))

    @http.route('/erpvn_hr_leave_management/holidays/view', type='http', auth="public")
    def view_holiday_list(self, **kwargs):
        action = request.env.ref("hr_holidays.hr_leave_action_my")
        return werkzeug.utils.redirect('/web#action=%s&model=hr.leave&view_type=list' % (action.id))

    @http.route('/leaveapproval/<employee_id>/<id>', type='http', auth='public', website=True)
    def time_off_request_page(self, *args, **kw):
        employee_id = int(kw['employee_id'])
        id = int(kw['id'])
        values = http.request.env['hr.leave'].sudo().search(
            [('employee_id', '=', employee_id), ('id', '=', id)])
        value = {
            'values': values,
        }
        return http.request.render('erpvn_hr_leave_management.time_off_request_page', value)

    @http.route('/approvalmail', type='http', auth='public', website=True,  csrf=False)
    def action_approve(self, *args, **post):
        holiday_id = int(post.get('hr_holidays'))
        holiday_obj = http.request.env['hr.leave'].sudo().search(
            [('id', '=', holiday_id)])
        if holiday_obj:
            if holiday_obj.holiday_status_id.leave_validation_type == 'manager':
                if holiday_obj.state == 'confirm':
                    value = {
                        'values': holiday_obj,
                    }
                    holiday_obj.action_approve()
                    template_id = request.env.ref(
                        'erpvn_hr_leave_management.leave_validation_mail')

                    template_id.send_mail(holiday_id, force_send=True)
                    return http.request.render('erpvn_hr_leave_management.submit')

                if holiday_obj.state == 'validate1':
                    value = {
                        'values': holiday_obj,
                    }
                    holiday_obj.action_validate()
                    template_id = request.env.ref(
                        'erpvn_hr_leave_management.leave_validation_mail')
                    template_id.send_mail(holiday_id, force_send=True)
                    return http.request.render('erpvn_hr_leave_management.validation_page', value)
            else:
                if holiday_obj.state == 'confirm':
                    value = {
                        'values': holiday_obj,
                    }
                    holiday_obj.action_approve()
                    template_id = request.env.ref(
                        'erpvn_hr_leave_management.leave_approval_mail')

                    template_id.send_mail(holiday_id, force_send=True)
                    return http.request.render('erpvn_hr_leave_management.submit')

    @http.route('/approvalvalidationmail/<employee_id>/<id>', type='http', auth='public', website=True)
    def action_approve_validate(self, *args, **kw):
        employee_id = int(kw['employee_id'])
        id = int(kw['id'])
        values = http.request.env['hr.leave'].sudo().search(
            [('employee_id', '=', employee_id), ('id', '=', id)])
        value = {
            'values': values,
        }
        return http.request.render('erpvn_hr_leave_management.validation_page', value)

    @http.route('/approvalvalidationmail', type='http', auth='public', website=True,  csrf=False)
    def action_validate(self, *args, **post):
        holiday_id = int(post.get('hr_holidays'))
        holiday_obj = http.request.env['hr.leave'].sudo().search(
            [('id', '=', holiday_id)])
        if holiday_obj:
            if holiday_obj.holiday_status_id.double_validation == True:
                if holiday_obj.state == 'validate1':
                    holiday_obj.action_validate()
                    template_id = request.env.ref(
                        'erpvn_hr_leave_management.leave_approval_mail')
                    template_id.send_mail(holiday_id, force_send=True)
                    return http.request.render('erpvn_hr_leave_management.submit')
            else:
                holiday_obj.action_validate()
                return http.request.render('erpvn_hr_leave_management.submit')

    @http.route('/refusemail', type='http', auth='public', website=True,  csrf=False)
    def action_refuse(self, *args, **post):
        holiday_id = int(post['hr_holiday'])
        holiday_obj = http.request.env['hr.leave'].sudo().search(
            [('id', '=', holiday_id)])
        if holiday_obj:
            if holiday_obj.holiday_status_id.double_validation == True:
                if holiday_obj.state in ('confirm', 'validate1'):
                    holiday_obj.action_refuse()
                    template_id = request.env.ref(
                        'erpvn_hr_leave_management.leave_rejection_mail')
                    template_id.send_mail(holiday_id, force_send=True)
                    return http.request.render('erpvn_hr_leave_management.submit')
            if holiday_obj.state in ('confirm'):
                holiday_obj.action_refuse()
                template_id = request.env.ref(
                    'erpvn_hr_leave_management.leave_rejection_mail')
                template_id.send_mail(holiday_id, force_send=True)
                return http.request.render('erpvn_hr_leave_management.submit')
