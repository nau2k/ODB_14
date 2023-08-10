
from odoo import http
from odoo.http import request,content_disposition
import mimetypes
import ast

class Binary(http.Controller):

    @http.route('/web/binary/download_subcontract', type='http', auth="public")
    def download_subcontract(self,model,field,id,info,filename=None, **data):
        context = dict(request.env.context)
        docids= eval(id)
        # data= ast.literal_eval(data.get('data'))
        # subcontract=request.env['hr.subcontract'].browse(docids)
        # contract= request.env['hr.contract'].search([('employee_id.name','=',subcontract.employee_id.name)])
        ir_action = request.env["ir.actions.report"]
        if info == 'salary':
            ir=ir_action.get_from_report_name('py3o_subcontract_salary','py3o').with_context(context)
        if info == 'Job':
            ir=ir_action.get_from_report_name('py3o_subcontract_position','py3o').with_context(context)
        else:
            ir=ir_action.get_from_report_name('py3o_subcontract','py3o').with_context(context)

        res, filetype = ir._render(docids, data)
        filename = ir.gen_report_download_filename(docids, data)
        if not filename.endswith(filetype):
            filename = "{}.{}".format(filename, filetype)
        content_type = mimetypes.guess_type("x." + filetype)[0]
        http_headers = [
            ("Content-Type", content_type),
            ("Content-Length", len(res)),
            ("Content-Disposition", content_disposition(filename)),
        ]
        return request.make_response(res, headers=http_headers)

    
    @http.route('/web/binary/download_contract', type='http', auth="public")
    def download_contract(self,model,field,id,filename=None, **data):
        context = dict(request.env.context)
        docids= eval(id)
        # data= ast.literal_eval(data.get('data'))
        ir_action = request.env["ir.actions.report"]

        ir=ir_action.get_from_report_name('py3o_contract','py3o').with_context(context)
        

        res, filetype = ir._render(docids, data)
        filename = ir.gen_report_download_filename(docids, data)
        if not filename.endswith(filetype):
            filename = "{}.{}".format(filename, filetype)
        content_type = mimetypes.guess_type("x." + filetype)[0]
        http_headers = [
            ("Content-Type", content_type),
            ("Content-Length", len(res)),
            ("Content-Disposition", content_disposition(filename)),
        ]
        return request.make_response(res, headers=http_headers)