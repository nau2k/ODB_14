# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request,content_disposition
import mimetypes

class Binary(http.Controller):

    @http.route('/web/binary/download_resignation', type='http', auth="public")
    def download_resignation(self,model,field,id,filename=None, **data):
        context = dict(request.env.context)
        docids= eval(id)
        # data= ast.literal_eval(data.get('data'))
        ir_action = request.env["ir.actions.report"]

        ir=ir_action.get_from_report_name('py3o_resignation','py3o').with_context(context)

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