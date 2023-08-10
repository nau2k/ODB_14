# -*- coding: utf-8 -*-
from pytz import utc
from odoo import models


class ResourceMixin(models.AbstractModel):
    _inherit = "resource.mixin"

    # override odoo's func.
    def list_leaves(self, from_datetime, to_datetime, calendar=None, domain=None):
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        attendances = calendar._attendance_intervals_batch(from_datetime, to_datetime, resource)[resource.id]
        leaves = calendar._leave_intervals_batch(from_datetime, to_datetime, resource, domain)[resource.id]
        result = []
        for start, stop, leave in (leaves & attendances):
            hours = ((stop - start).total_seconds() / 3600) - calendar._get_breaking_hours(leave, start, stop, calendar=calendar)
            result.append((start.date(), hours, leave))
        return result