# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    mo_lv = fields.Integer(string='Lv', default=1, readonly=True)
    bom_time_produce = fields.Float('Time Produce (mins)', default=0.0, store=True, readonly=True)
    bom_total_time = fields.Float('Total Time (mins)', default=0.0, store=True, readonly=True)
    master_mo_id = fields.Many2one('mrp.production', string="Master MO", store=True, readonly=True)
    productivity_count = fields.Integer("Count of productivity", compute='_compute_productivity')
    categ_id = fields.Many2one(string='Product Category', comodel_name='product.category',
        related='product_id.categ_id', readonly=True, store=True)
    bom_type = fields.Selection(string='BoM Type', related='bom_id.type', readonly=True, store=True)

    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', store=True)
    item_complete_name = fields.Char('Item Path', compute='_compute_item_complete_name', store=True)
    item_complete_id = fields.Char('Item ID Path', compute='_compute_item_complete_name', store=True)
    production_complete_name = fields.Char('Name Path', compute='_compute_production_complete_name', store=True)

    parent_id = fields.Many2one('mrp.production', string="Parent MO", index=True, ondelete='cascade', store=True)
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('mrp.production', 'parent_id', 'Child Categories')

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive productions.'))

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for production in self:
            if production.parent_id:
                production.complete_name = '%s / %s' % (production.parent_id.complete_name, production.name)
            else:
                production.complete_name = production.name

    @api.depends('parent_id.product_id')
    def _compute_item_complete_name(self):
        for production in self:
            if production.parent_id:
                production.item_complete_name = '%s / %s' % (production.parent_id.item_complete_name, production.product_id.display_name)
                production.item_complete_id = '%s/%s' % (production.parent_id.item_complete_id, str(production.product_id.id))
            else:
                production.item_complete_name = production.product_id.display_name
                production.item_complete_id = str(production.product_id.id)

    @api.depends('parent_id.product_id')
    def _compute_production_complete_name(self):
        for production in self:
            if production.parent_id:
                production.production_complete_name = '%s / %s' % (production.parent_id.production_complete_name, production.name)
            else:
                production.production_complete_name = production.name

    # def _post_mo_merging_adjustments(self, vals):
    #     """Called when a new MO is merged onto existing one for adjusting the
    #     needed values according this merging.
    #     :param self: Single record of the target record where merging.
    #     :param vals: Dictionary with the new record values.
    #     """
    #     self.ensure_one()
    #     new_vals = {"origin": (self.origin or "") + ",%s" % vals["origin"]}
    #     if vals.get("move_dest_ids"):
    #         new_vals["move_dest_ids"] = vals["move_dest_ids"]
    #         self.move_finished_ids.move_dest_ids = vals["move_dest_ids"]
    #     self.write(new_vals)

    def _get_grouping_target_domain(self, vals):
        """Get the domain for searching manufacturing orders that can match
        with the criteria we want to use.
        :param vals: Values dictionary of the MO to be created.
        :return: Odoo domain.
        """
        domain = [
            ("product_id", "=", vals["product_id"]),
            ("picking_type_id", "=", vals["picking_type_id"]),
            ("bom_id", "=", vals.get("bom_id", False)),
            ("company_id", "=", vals.get("company_id", False)),
            ("state", "in", ["draft", "confirmed"]),
        ]
        if vals.get("routing_id"):
            domain.append({("routing_id", "=", vals.get("routing_id"))})
        if not vals.get("date_planned_finished"):
            return domain
        date = fields.Datetime.from_string(vals["date_planned_finished"])
        pt = self.env["stock.picking.type"].browse(vals["picking_type_id"])
        date_end = date.replace(hour=pt.mo_grouping_max_hour, minute=0, second=0)
        if date.hour >= pt.mo_grouping_max_hour:
            date_end += relativedelta(days=1)
        date_start = date_end - relativedelta(days=pt.mo_grouping_interval)
        domain += [
            ("date_planned_finished", ">", fields.Datetime.to_string(date_start)),
            ("date_planned_finished", "<=", fields.Datetime.to_string(date_end)),
        ]
        return domain

    def _find_grouping_target(self, vals):
        """Return the matching order for grouping.
        :param vals: Values dictionary of the MO to be created.
        :return: Target manufacturing order record (or empty record).
        """
        return self.env["mrp.production"].search(self._get_grouping_target_domain(vals), limit=1)

    def _get_time_produce(self):
        res = sum(self.workorder_ids.mapped('duration_expected'))
        child_mo_ids = self.env['mrp.production'].search([('parent_id', 'in', self.ids)])
        for child_mo_id in child_mo_ids:
            if child_mo_id.workorder_ids:
                res += child_mo_id._get_time_produce()
        return res

    def _compute_time_produce(self):
        time_produce, total_time_produce = 0.0, 0.0
        if self.workorder_ids:
            time_produce = sum(self.workorder_ids.mapped('duration_expected'))
        total_time_produce = self._get_time_produce()
        self.write({'bom_time_produce': time_produce, 'bom_total_time': total_time_produce})
        if self.parent_id:
            self.parent_id._compute_time_produce()

    def write(self, values):
        if values.get('move_raw_ids', False):
            # update sequence when add new components in MO.
            sequence = 10
            is_checked_raw_id = False
            for item in values.get('move_raw_ids'):
                if len(item) == 3:
                    if isinstance(item[-1], dict):
                        if item[-1].get('sequence', False):
                            if not is_checked_raw_id:
                                is_checked_raw_id = True
                                if self.move_raw_ids:
                                    sequence = max(list(set(self.move_raw_ids.mapped('sequence')))) + 10
                            item[-1]['sequence'] = sequence
                            sequence += 10
        return super(MrpProduction, self).write(values)

    def _get_moves_raw_values(self):
        move_ids = super(MrpProduction, self)._get_moves_raw_values()
        for production_id in self:
            seq = 10
            for move_id in move_ids:
                if move_id.get('raw_material_production_id', False) == production_id.id:
                    move_id.update({'sequence': seq})
                    seq += 10
        return move_ids

    @api.depends('workorder_ids.time_ids')
    def _compute_productivity(self):
        for production in self:
            production.productivity_count = len(production.workorder_ids.time_ids)

    def action_view_productivities(self):
        self.ensure_one()
        workorder_ids = self.workorder_ids.ids
        action = {
            'res_model': 'mrp.workcenter.productivity',
            'type': 'ir.actions.act_window',
            'name': _("Productivities"),
            'domain': [('workorder_id', 'in', workorder_ids)],
            'view_mode': 'tree',
        }
        return action

    def button_mark_done(self):
        for production in self:
            if not production.move_raw_ids:
                raise UserError(_("There is no component in production order %(production_name)s!", production_name=production.name))
            
            # add lot/serial number for byproducts.
            for line in production.move_byproduct_ids.move_line_ids.filtered(lambda x: not x.lot_id and x.qty_done > 0):
                line._create_and_assign_production_lot()
        return super(MrpProduction, self).button_mark_done()

    def open_add_raw(self):
        picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'internal'), ('barcode', '=', 'WH-PC')])
        action = {
            'name': _('Add Materials'),
            'view_mode': 'form',
            'res_model': 'stock.picking.wizard',
            'view_id': self.env.ref('erpvn_mrp_management.view_stock_picking_wizard_form').id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_partner_id': self.env.user.partner_id.id,
                'default_picking_type_id': picking_type_id.id if picking_type_id else False,
                'default_location_id': picking_type_id.default_location_src_id.id if picking_type_id else False,
                'default_location_dest_id': self.location_src_id.id if self.location_src_id else False,
                'default_origin': self.name,
                'default_mo_id': self.id,
                'default_state': 'draft',
            },
        }
        return action

    @api.model
    def create(self, vals):
        vals.update({'name': self.env['ir.sequence'].next_by_code('sequence.mrp.production.code') or _('New')})
        res = super(MrpProduction, self).create(vals)
        return res

    def _do_reset_sequence(self):
        sequences = self.env['ir.sequence'].search([('code', '=', 'sequence.mrp.production.code')])
        sequences.write({'number_next_actual': 1}) 

    def action_confirm(self):
        self._check_company()

        if self.filtered(lambda x: not x.move_raw_ids):
            raise UserError(_("Add some materials to consume before marking these MO(s) as to do:\n+ ") \
                + '\n+ '.join(self.filtered(lambda x: not x.move_raw_ids).mapped('name')))

        return super(MrpProduction, self).action_confirm()

    def button_plan_reversed(self, date_finish):
        orders_to_plan = self.filtered(lambda order: not order.is_planned)
        orders_to_confirm = orders_to_plan.filtered(lambda mo: mo.state == 'draft')
        orders_to_confirm.action_confirm()
        orders_to_plan._plan_workorder_reversed(date_finish)
        return True

    def _plan_workorder_reversed(self, in_date_finish):
        time_produce = 0.0
        date_start = datetime.datetime.now()
        date_finish = in_date_finish

        for production_id in reversed(self):
            if production_id.workorder_ids:
                time_produce = sum(production_id.workorder_ids.mapped('duration_expected'))
                date_start = in_date_finish - datetime.timedelta(minutes=time_produce)

                workcenter_is_not_available = False
                for workorder_id in reversed(production_id.workorder_ids):
                    workcenters = workorder_id.workcenter_id | workorder_id.workcenter_id.alternative_workcenter_ids

                    best_finished_date = datetime.datetime.max
                    vals = {}
                    for workcenter in workcenters:
                        # compute theoretical duration
                        if workorder_id.workcenter_id == workcenter:
                            duration_expected = workorder_id.duration_expected
                        else:
                            duration_expected = workorder_id._get_duration_expected(alternative_workcenter=workcenter)

                        from_date, to_date = workcenter._get_reversed_first_available_slot(date_finish, duration_expected)
                        # If the workcenter is unavailable, try planning on the next one
                        if not from_date:
                            continue
                        # Check if this workcenter is better than the previous ones
                        if to_date and to_date < best_finished_date:
                            best_start_date = from_date
                            best_finished_date = to_date
                            best_workcenter = workcenter
                            vals.update({
                                'workcenter_id': workcenter.id,
                                'duration_expected': duration_expected,
                            })

                    # If none of the workcenter are available, raise
                    if best_finished_date == datetime.datetime.max:
                        workcenter_is_not_available = True
                        break
                        # duy.bui on Apr 5, 2023: skip workorder for temporary.
                        # raise UserError(_('Please check the workcenter availabilities.'))

                    # Create leave on chosen workcenter calendar
                    leave = self.env['resource.calendar.leaves'].create({
                        'name': workorder_id.display_name,
                        'calendar_id': best_workcenter.resource_calendar_id.id,
                        'date_from': best_start_date,
                        'date_to': best_finished_date,
                        'resource_id': best_workcenter.resource_id.id,
                        'time_type': 'other',
                        'state':'waiting',
                    })
                    vals['leave_id'] = leave.id
                    workorder_id.write(vals)

                    # need modify: check ready_to_produce in bom for def _plan_workorders(self, replan=False) in future.
                    if production_id.bom_id:
                        if production_id.bom_id.ready_to_produce == 'all_available':
                            date_finish = best_start_date

                if workcenter_is_not_available:
                    date_start = datetime.datetime.now()
                    date_finish = date_start + datetime.timedelta(minutes=time_produce)
                else:
                    date_start = min(production_id.workorder_ids.mapped('date_planned_start'))
                    date_finish = max(production_id.workorder_ids.mapped('date_planned_finished'))
            else:
                # no work order in MO.
                date_start = date_finish
            production_id.with_context(force_date=True).write({
                'date_planned_start': date_start,
                'date_planned_finished': date_finish,
            })

    def _action_print_picking(self):
        mo_ids = self.filtered(lambda x: x.picking_ids)
        if mo_ids:
            return  {
                        'name': _('Print Picking'),
                        'view_mode': 'form',
                        'res_model': 'print.picking.wizard',
                        'view_id': self.env.ref('erpvn_mrp_management.wizard_print_picking').id,
                        'type': 'ir.actions.act_window',
                        'target': 'new',
                        'context': {
                            'default_picking_ids': mo_ids.picking_ids.ids,
                        },
                    }
        
    # def _log_downside_manufactured_quantity(self, moves_modification, cancel=False):

    #     def _keys_in_sorted(move):
    #         # pass error message to sys user instead of technical user
    #         odoo_uid = self.sudo().env['res.users'].browse(1)
    #         return (move.picking_id.id, odoo_uid.id)

    #     def _keys_in_groupby(move):
    #         odoo_uid = self.sudo().env['res.users'].browse(1)
    #         return (move.picking_id, odoo_uid)

    #     def _render_note_exception_quantity_mo(rendering_context):
    #         values = {
    #             'production_order': self,
    #             'order_exceptions': rendering_context,
    #             'impacted_pickings': False,
    #             'cancel': cancel
    #         }
    #         return self.env.ref('mrp.exception_on_mo')._render(values=values)

    #     documents = self.env['stock.picking']._log_activity_get_documents(moves_modification, 'move_dest_ids', 'DOWN', _keys_in_sorted, _keys_in_groupby)
    #     documents = self.env['stock.picking']._less_quantities_than_expected_add_documents(moves_modification, documents)
    #     self.env['stock.picking']._log_activity(_render_note_exception_quantity_mo, documents)
