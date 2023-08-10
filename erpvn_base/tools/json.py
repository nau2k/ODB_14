import datetime
import json

from odoo import fields, models
from odoo.tools import ustr


class ResponseEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            if isinstance(obj, datetime.datetime):
                return fields.Datetime.to_string(obj)
            return fields.Date.to_string(obj)
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode()
        return ustr(obj)


class RecordEncoder(ResponseEncoder):
    def default(self, obj):
        if isinstance(obj, models.BaseModel):
            return obj.name_get()
        return ResponseEncoder.default(self, obj)
