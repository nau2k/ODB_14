# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

class MrpWorkorder(models.Model):
    _name = 'mrp.workorder'
    _inherit = ['mrp.workorder','mail.thread']

    mo_lv = fields.Integer(string='Lv', related='production_id.mo_lv', readonly=True, store='True')
    available_capacity = fields.Float(_('WC Weekly Available Capacity'), related='workcenter_id.available_capacity', store='True', group_operator="avg")
    capacity_requirements = fields.Float(_('WO Capacity Requirements'), compute='_wo_capacity_requirement', store='True')
    sequence = fields.Integer('Sequence', compute='_compute_sequence', store=True)
    barcode = fields.Char(string="Barcode", compute='_get_barcode', store=True)
    percent_progressed = fields.Float(string='Qty Progress (%)', compute='_get_progress', store=True, readonly=True, group_operator="avg")
    time_progressed = fields.Float(string='Time Progress (%)', compute='_get_progress', store=True, readonly=True,
        help="Less than 100%, hign capacity.\nOtherwise, low capacity.")

    qty_production = fields.Float('Original Quantity', readonly=True, related='production_id.product_qty', store=True)

    data_type = fields.Selection([('normal','Normal'), ('no_operation','No Operation'), ('error','Error')], copy=False, default='normal', required=True)

    is_last_wo = fields.Boolean(string=_('Is Last Work Order?'), default=False, help="For check out in scan MRP.")
    state = fields.Selection([
        ('pending', 'Paused'),
        ('ready', 'Ready'),
        ('progress', 'In Progress'),
        ('done', 'Finished'),
        ('cancel', 'Cancelled')], string=_('Status'), default='ready', copy=False, readonly=True)
    block_reson_id = fields.Many2one('mrp.workcenter.productivity.loss', "Block Reason", ondelete='restrict')
    note = fields.Text('Note')

    @api.depends('qty_production', 'qty_produced')
    def _compute_qty_remaining(self):
        for wo in self:
            rounding = wo.production_id.product_uom_id.rounding if wo.production_id.product_uom_id else 0.001
            wo.qty_remaining = float_round(wo.qty_production - wo.qty_produced, precision_rounding=rounding)

    def write(self, vals):
        if 'is_last_wo' in vals:
            if vals.get('is_last_wo'):
                for wo_id in self.production_id.workorder_ids:
                    if wo_id.sequence > self.sequence and wo_id.state in ('ready', 'pending'):
                        wo_id.update({'state': 'cancel'})
                    if wo_id.id != self.id and wo_id.is_last_wo:
                        wo_id.update({'is_last_wo': False})
            else:
                if len(self.production_id.workorder_ids.filtered(lambda x: x.is_last_wo and x.id != self.id)) > 1:
                    for wo_id in self.production_id.workorder_ids.filtered(lambda x: x.is_last_wo and x.id != self.id)[:-1]: # leave the largest seqence is last wo.
                        wo_id.update({'is_last_wo': False})

        if 'production_id' in vals:
            if not vals.get('production_id', False):
                vals.pop('production_id')

        if self.env.context.get('bypass_duration_calculation', False):
            if 'date_planned_start' in vals and self.filtered(lambda x: x.date_planned_start):
                del vals['date_planned_start']
            if 'date_planned_finished' in vals and self.filtered(lambda x: x.date_planned_finished):
                del vals['date_planned_finished']

        return super(MrpWorkorder, self).write(vals)

    def update_sequence(self):
        wo_ids = self.production_id.workorder_ids.filtered(lambda x: x.state in ('ready', 'pending', 'progress'))
        if wo_ids:
            max_seq = max(wo_ids.mapped('sequence')) # not includes wo_id.state == 'done'
            for wo_id in wo_ids:
                if wo_id.sequence == max_seq:
                    wo_id.update({'is_last_wo': True})
                elif wo_id.is_last_wo:
                    wo_id.update({'is_last_wo': False})

    def button_unblock(self):
        self.ensure_one()

        if self.state != 'cancel':
            raise ValidationError(_("It has already been unblocked."))

        timeline_obj = self.env['mrp.workcenter.productivity']
        self.update({'state': 'ready', 'block_reson_id': False})
        for timeline in timeline_obj.search([('workorder_id', '=', self.id), ('date_end', '=', False)], limit=None):
            timeline.write({'date_end': datetime.now()})
        self.update_sequence()
        return True

    def show_block_reason_wizard_form(self):
        self.ensure_one()

        if self.state in ('cancel', 'progress', 'done'):
            raise ValidationError(_('Can not block in %s status!') % dict(self._fields['state'].selection).get(self.state))

        wz_form = self.env.ref('erpvn_hr_mrp.mrp_workorder_block_reason_wizard_form', False)
        return {
            'name': 'Block Workorder',
            'type': 'ir.actions.act_window', 
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'block.reason.wizard',
            'views': [(wz_form.id, 'form')],
            'view_id': wz_form.id,
            'target': 'new',
            'context': {'default_workorder_id': self.id},
        }

    @api.depends('duration_expected')
    def _wo_capacity_requirement(self):
        for workorder in self:
            workorder.capacity_requirements = (workorder.duration_expected) / 60
        return True

    @api.depends('operation_id')
    def _compute_sequence(self):
        list_seqs = []
        for workorder in self:
            routing_seq = workorder.operation_id.sequence or 10000
            list_seqs.append(routing_seq)

            if list_seqs and list_seqs.count(routing_seq) > 1:
                routing_seq = routing_seq + list_seqs.count(routing_seq) - 1

            # production_seqs = workorder.production_id.workorder_ids.mapped('sequence')
            # if production_seqs and routing_seq in production_seqs:
            #     routing_seq = max(production_seqs) + 10

            workorder.sequence = routing_seq

    @api.depends('production_id', 'sequence')
    def _get_barcode(self):
        for workorder in self:
            workorder.barcode = str(workorder.production_id.name) + '-' + str(workorder.sequence)
    
    # @api.model
    # def create(self, values):
    #     res = super(MrpWorkorder, self).create(values)
    #     self.production_id._compute_time_produce()
    #     return res

    # def _update_component_quantity(self):
    #     # if self.component_tracking == 'serial':
    #     #     self.qty_done = self.product_id.uom_id._compute_quantity(1, self.product_uom_id, rounding_method='HALF-UP')
    #     #     return
    #     move = self.move_id
    #     # Compute the new quantity for the current component
    #     rounding = move.product_uom.rounding
    #     new_qty = self._prepare_component_quantity(move, self.qty_producing)

    #     # In case the production uom is different than the workorder uom
    #     # it means the product is serial and production uom is not the reference
    #     new_qty = self.product_uom_id._compute_quantity(
    #         new_qty,
    #         self.production_id.product_uom_id,
    #         round=False
    #     )
    #     qty_todo = float_round(new_qty, precision_rounding=rounding)
    #     qty_todo = qty_todo - move.quantity_done
    #     if self.move_line_id:
    #         qty_todo = min(self.move_line_id.product_uom_qty, qty_todo)
    #     self.qty_done = qty_todo or 1

    def button_start(self):
        temp = {}
        if self.production_id.move_byproduct_ids:
            for move_line in self.production_id.move_byproduct_ids.move_line_ids:
                if move_line:
                    temp[move_line.product_id.id] = move_line.qty_done

        # prevent update 'date_planned_start' production's field.
        if self.production_id.date_planned_start:
            self.env.context = dict(self.env.context)
            self.env.context.update({'bypass_duration_calculation': True,})
            
        res = super().button_start()
        
        # tạm thời commnet lại 
        # if self.product_tracking == 'serial' :
        #     self._update_component_quantity()
        if self.production_id.move_byproduct_ids:
            if temp:
                for move_line in self.production_id.move_byproduct_ids.move_line_ids:
                    if move_line.product_id.id in temp:
                        qty_done = temp[move_line.product_id.id]
                    else:
                        qty_done = 0.0
                    move_line.update({'qty_done': qty_done})
            else:
                if self.qty_produced == 0.0:
                    for move in self.production_id.move_byproduct_ids:
                        move.update({'quantity_done': 0.0})
        return res

    def button_pending(self):
        for log in self.time_ids.filtered(lambda x: not x.date_end):
            log.update({'state': 'pause'})
        res = super(MrpWorkorder, self).button_pending()
        self.update({'state': 'ready'})
        return res

    def _start_nextworkorder(self):
        if self.state == 'done' and self.next_work_order_id.state == 'pending':
            super(MrpWorkorder, self)._start_nextworkorder()
            self.next_work_order_id.state = 'pending'

    def button_finish(self):
        for log in self.time_ids.filtered(lambda x: not x.date_end):
            log.update({'state': 'done'})
        
        # prevent update 'date_planned_start' field.
        self.env.context = dict(self.env.context)
        self.env.context.update({'bypass_duration_calculation': True,})

        res = super(MrpWorkorder, self).button_finish()
        return res

    @api.depends('qty_produced', 'qty_production', 'duration', 'duration_expected')
    def _get_progress(self):
        for wo_id in self:
            time_progressed, percent_progressed = 0.0, 0.0
            if wo_id.duration_expected:
                time_progressed = 100.0 * wo_id.duration / wo_id.duration_expected

            if wo_id.qty_production:
                percent_progressed = 100.0 * wo_id.qty_produced / wo_id.qty_production

            wo_id.time_progressed = time_progressed
            wo_id.percent_progressed = percent_progressed

    def end_previous(self, doall=False):
        """overload:  This will close all open time lines on the open work orders"""
        # TDE CLEANME
        timeline_obj = self.env['mrp.workcenter.productivity']
        domain = [('workorder_id', 'in', self.ids), ('date_end', '=', False)]
        not_productive_timelines = timeline_obj.browse()
        for timeline in timeline_obj.search(domain, limit=None if doall else 1):
            wo = timeline.workorder_id
            if wo.duration_expected <= wo.duration:
                if timeline.loss_type == 'productive':
                    not_productive_timelines += timeline
                timeline.write({'date_end': fields.Datetime.now()})
            else:
                maxdate = fields.Datetime.from_string(timeline.date_start) + relativedelta(minutes=wo.duration_expected - wo.duration)
                enddate = datetime.now()
                if maxdate > enddate:
                    timeline.write({'date_end': enddate})
                else:
                    timeline.write({'date_end': maxdate})
        if not_productive_timelines:
            loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'performance')], limit=1)
            if not len(loss_id):
                raise UserError(_("You need to define at least one unactive productivity loss in the category 'Performance'. Create one from the Manufacturing app, menu: Configuration / Productivity Losses."))
            not_productive_timelines.write({'loss_id': loss_id.id})
        return True
    
    def action_update_progress(self):
        for record in self:
            record._get_progress()