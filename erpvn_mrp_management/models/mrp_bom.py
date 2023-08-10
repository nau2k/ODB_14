# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict
from odoo.tools import float_round, float_compare
import math

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    active = fields.Boolean(tracking=True)
    code = fields.Char(required=True, tracking=True)
    type = fields.Selection(tracking=True)
    product_tmpl_id = fields.Many2one(tracking=True, ondelete='cascade')
    product_id = fields.Many2one(tracking=True)
    product_qty = fields.Float(tracking=True)
    product_uom_id = fields.Many2one(tracking=True)
    ready_to_produce = fields.Selection(tracking=True)
    picking_type_id = fields.Many2one(tracking=True)
    consumption = fields.Selection(tracking=True)

    template_id = fields.Many2one(string='Template Id', comodel_name='mrp.bom', tracking=True)
    child_template_ids = fields.One2many(string='Child Template Id', comodel_name='mrp.bom', inverse_name='template_id')
    categ_id = fields.Many2one(string='Product Category', comodel_name='product.category', related='product_tmpl_id.categ_id', readonly=True, store=True, tracking=True)

    time_produce = fields.Float('Time Produce (mins)', readonly=True, tracking=True)
    total_time = fields.Float('Total Time (mins)', readonly=True, tracking=True)
    total_time_unit = fields.Float('Total Time Unit (mins)', compute='_compute_total_time_unit', store=True)
    
    price_produce = fields.Float('Price Produce', readonly=True)
    total_price_produce = fields.Float('Total Price', readonly=True)
    mrp_workingtime_workcenter_ids = fields.One2many('mrp.workingtime.workcenter', 'bom_id', string='Working Time Workcenters', readonly=True)
    mrp_component_line_ids = fields.One2many('mrp.component.line', 'bom_id', string='Component Line', readonly=True)
    is_update_bom = fields.Boolean(default=False, string="Is Update BOM?", help="Mark BOM as need to be update in cron job")
    bom_extra_plan_ids = fields.One2many('bom.extra.plan', 'parent_bom_id', 'BOM Extra Plan', copy=True)
    has_routing = fields.Boolean(string='Has Routing?', compute='_compute_has_routing', store=True)

    _sql_constraints = [
        ('code_bom_uniq', 'unique (code)', 'The Reference of the BoM must be unique!')
    ]

    @api.depends('operation_ids')
    def _compute_has_routing(self):
        for bom in self:
            bom.has_routing = bool(bom.operation_ids)

    @api.depends('total_time','product_qty','product_uom_id')
    def _compute_total_time_unit(self):
        for bom in self:
            qty = bom.product_tmpl_id and bom.product_uom_id._compute_quantity(
                bom.product_qty, bom.product_tmpl_id.uom_id, rounding_method='HALF-UP') or 1
            bom.total_time_unit = bom.total_time > 0 and bom.total_time / qty 

    @api.onchange('product_id')
    def _onchange_bom_code(self):
        if self.product_id:
            self.code = self.product_id.default_code

    def get_operation_ids(self):
        temp, result = [], []

        def _resursive(bom_id, lv=1, parent_cycle=1.0):
            if bom_id.operation_ids.ids:
                k = str(bom_id.id) + '-' + str(lv) + '-' + str(parent_cycle)
                temp.append({k: bom_id.operation_ids.ids})
            for line_id in bom_id.bom_line_ids:
                if line_id.product_id.bom_ids:
                    running_bom = line_id.product_id.bom_ids.sorted('version', reverse=True)[0]
                    cycle_number = tools.float_round((line_id.product_qty / bom_id.product_qty or 1.0), precision_digits=0, rounding_method='UP')
                    _resursive(running_bom, lv=lv+1, parent_cycle=parent_cycle*cycle_number)

        _resursive(self, lv=1, parent_cycle=1.0)

        poo = {}
        for i in temp:
            for k,v in i.items():
                bom_id, lv, cycle = k.split('-')
                if bom_id in list(map(lambda x: x.split('-')[0], poo.keys())):
                    existed_key = list(filter(lambda x: x.split('-')[0] == str(bom_id), poo.keys()))[0]
                
                    new_cycle = float(existed_key.split('-')[-1]) + float(cycle)
                    new_key = str(bom_id) + '-' + str(new_cycle)

                    tem = poo[existed_key] + v
                    del poo[existed_key]
                    poo.update({new_key: list(set(tem))})
                else:
                    poo.update({str(bom_id) + '-' + str(cycle): v})

        for k, v in poo.items():
            bom_id, cycle = k.split('-')
            result.append({'bom_id': int(bom_id), 'cycle': float(cycle), 'operations': list(v)})
        return result

    def get_component_ids(self):
        def _resursive(bom_id, lv=1, parent_cycle=1.0):
            if bom_id.bom_line_ids.ids:
                k = str(bom_id.id) + '-' + str(lv) + '-' + str(parent_cycle)
                temp.append({k: bom_id.bom_line_ids.ids})
            for line_id in bom_id.bom_line_ids:
                if line_id.product_id.bom_ids:
                    running_bom = line_id.product_id.bom_ids.sorted('version', reverse=True)[0]
                    cycle_number = line_id.technical_qty / bom_id.product_qty or 1.0
                    _resursive(running_bom, lv=lv+1, parent_cycle=parent_cycle*cycle_number)

        temp, result = [], []
        _resursive(self, lv=1, parent_cycle=1.0)
        poo = {}
        for i in temp:
            for k,v in i.items():
                bom_id, lv, cycle = k.split('-')
                if bom_id in list(map(lambda x: x.split('-')[0], poo.keys())):
                    existed_key = list(filter(lambda x: x.split('-')[0] == str(bom_id), poo.keys()))[0]
                    new_cycle = float(existed_key.split('-')[-1]) + float(cycle)
                    new_key = str(bom_id) + '-' + str(new_cycle)
                    tem = poo[existed_key] + v
                    del poo[existed_key]
                    poo.update({new_key: list(set(tem))})
                else:
                    poo.update({str(bom_id) + '-' + str(cycle): v})

        for k, v in poo.items():
            bom_id, cycle = k.split('-')
            result.append({'bom_id': int(bom_id), 'cycle': float(cycle), 'components': list(v)})
        return result

    def _check_existed_bom_code(self, bom_vals):
        for val in bom_vals:
            if not val.get('code', False):
                raise ValidationError(_("Reference is required field!"))
            if self._context.get('is_not_create_by_duplicate', False):
                if self.env['mrp.bom'].search_count([('code', '=', val.get('code'))]) > 0:
                    raise ValidationError(_("Reference '%s' already existed!")%(val.get('code')))

    @api.model_create_multi
    def create(self, bom_vals):
        if type(bom_vals) == list:
            self._check_existed_bom_code(bom_vals)
        for val in bom_vals:
            val.update({'is_update_bom': True})

        results = super(MrpBom, self).create(bom_vals)
        return results

    def write(self, bom_vals):
        if self._context.get('no_update_bom', False):
            return True

        if type(bom_vals) == list:
            self._check_existed_bom_code(bom_vals)

        if not self._context.get('is_updated_bom', False) and bom_vals.get('bom_line_ids', []):
            bom_vals.update({'is_update_bom': True})

        for lst in bom_vals.get('bom_line_ids', []):
            if len(lst) > 1 and lst[0] == 2:
                bom_line = self.env['mrp.bom.line'].browse(lst[1])
                self.env['mrp.bom.line']._log_message(bom_line.bom_id, bom_line, {'action': 'unlink'})
            elif len(lst) > 1 and lst[0] == 0:
                msg_vals = lst[2].copy()
                msg_vals['action'] = 'create'
                bom_id = self
                self.env['mrp.bom.line']._log_message(bom_id, False, msg_vals)

        for lst in bom_vals.get('bom_extra_plan_ids', []):
            if len(lst) > 1 and lst[0] == 2:
                extra_line = self.env['bom.extra.plan'].browse(lst[1])
                self.env['mrp.bom.line']._log_message(extra_line.parent_bom_id, extra_line, {'action': 'unlink', 'model': 'extra'})
            elif len(lst) > 1 and lst[0] == 0:
                msg_vals = lst[2].copy()
                msg_vals['action'] = 'create'
                msg_vals['model'] = 'extra'
                bom_id = self
                self.env['mrp.bom.line']._log_message(bom_id, False, msg_vals)

        return super(MrpBom, self).write(bom_vals)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        if not default.get('code', False):
            if self.code and self.search_count([('code', '=', self.code)]):
                bom_code, num = '', 0
                if self.product_id:
                    bom_code = self.product_id.get_bom_code()
                else:
                    temp_code = self.code + ' (' + str(num) + ')'
                    while self.search_count([('code', '=', temp_code)]):
                        num += 1
                        temp_code = bom_code + ' (' + str(num) + ')'
                    bom_code = temp_code
                default.update({'code': bom_code})
        return super(MrpBom, self).copy(default)

    def _get_bom_component_cost(self, bom_coefficient):
        res = 0.0
        for line_id in self.bom_line_ids:
            if line_id.product_id.bom_ids:
                running_bom = line_id.product_id.bom_ids.sorted('version', reverse=True)[0]
                bom_coefficient = line_id.product_qty / running_bom.product_qty
                child_res = line_id.product_id._get_bom_component_cost(running_bom, bom_coefficient)
                res += child_res
            else:
                res += (line_id.product_id.standard_price * line_id.product_qty * bom_coefficient)
        return res

    def compute_bom_cost(self):
        self.ensure_one()
        return self._get_bom_component_cost(bom_coefficient=1)

    def _check_valid_template_bom(self):
        pass

    def _check_bom_error(self):
        return defaultdict(list)

    def explode(self, product, quantity, picking_type=False):
        """
            Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
            Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
            and converted into its UoM
        """
        from collections import defaultdict

        graph = defaultdict(list)
        V = set()

        def check_cycle(v, visited, recStack, graph):
            visited[v] = True
            recStack[v] = True
            for neighbour in graph[v]:
                if visited[neighbour] == False:
                    if check_cycle(neighbour, visited, recStack, graph) == True:
                        return True
                elif recStack[neighbour] == True:
                    return True
            recStack[v] = False
            return False

        product_ids = set()
        product_boms = {}
        def update_product_boms():
            products = self.env['product.product'].browse(product_ids)
            product_boms.update(self._get_product2bom(products, bom_type='phantom',
                picking_type=picking_type or self.picking_type_id, company_id=self.company_id.id))
            # Set missing keys to default value
            for product in products:
                product_boms.setdefault(product, self.env['mrp.bom'])

        boms_done = [(self, {'qty': quantity, 'product': product, 'original_qty': quantity, 'parent_line': False})]
        lines_done = []
        V |= set([product.product_tmpl_id.id])

        bom_lines = []
        for bom_line in self.bom_line_ids:
            product_id = bom_line.product_id
            V |= set([product_id.product_tmpl_id.id])
            graph[product.product_tmpl_id.id].append(product_id.product_tmpl_id.id)
            bom_lines.append((bom_line, product, quantity, False))
            product_ids.add(product_id.id)
        update_product_boms()
        product_ids.clear()
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]

            if current_line._skip_bom_line(current_product):
                continue

            line_quantity = current_qty * current_line.technical_qty
            if float_compare(current_line.multiple_qty, 0, precision_rounding=current_line.product_uom_id.rounding) > 0:
                num_qty = int(math.ceil(current_line.product_qty * current_qty / current_line.multiple_qty)) * current_line.multiple_qty
                line_quantity = num_qty * (100 / float(current_line.product_loss))

            if not current_line.product_id in product_boms:
                update_product_boms()
                product_ids.clear()
            bom = product_boms.get(current_line.product_id)
            if bom:
                converted_line_quantity = current_line.product_uom_id._compute_quantity(line_quantity / bom.product_qty, bom.product_uom_id)
                bom_lines += [(line, current_line.product_id, converted_line_quantity, current_line) for line in bom.bom_line_ids]
                for bom_line in bom.bom_line_ids:
                    graph[current_line.product_id.product_tmpl_id.id].append(bom_line.product_id.product_tmpl_id.id)
                    if bom_line.product_id.product_tmpl_id.id in V and check_cycle(bom_line.product_id.product_tmpl_id.id, {key: False for  key in V}, {key: False for  key in V}, graph):
                        raise UserError(_('Recursion error!  A product with a Bill of Material should not have itself in its BoM or child BoMs!'))
                    V |= set([bom_line.product_id.product_tmpl_id.id])
                    if not bom_line.product_id in product_boms:
                        product_ids.add(bom_line.product_id.id)
                boms_done.append((bom, {'qty': converted_line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': current_line}))
            else:
                # We round up here because the user expects that if he has to consume a little more, the whole UOM unit
                # should be consumed.
                rounding = current_line.product_uom_id.rounding
                line_quantity = float_round(line_quantity, precision_rounding=rounding, rounding_method='UP')
                lines_done.append((current_line, {'qty': line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': parent_line}))

        return boms_done, lines_done

    def _get_mrp_comp_line_query(self):
        return """
            SELECT
                res.p_id AS product_id, SUM(res.p_qty) AS bom_qty, SUM(res.res_qty) AS need_qty
            FROM (
                SELECT
                    component.id AS c_id,
                    component.bom_id AS b_id,
                    component.product_id AS p_id,
                    component.product_qty * %(cycle)s AS p_qty,
                    component.multiple_qty AS m_qty,
                    component.product_loss AS p_los,
                    CASE
                        WHEN
                            component.multiple_qty <= 0.0 AND component.product_loss > 0.0 
                        THEN
                            component.product_qty * (100.0 / component.product_loss) * %(cycle)s
                        WHEN
                            component.multiple_qty > 0.0 AND component.product_loss > 0.0
                        THEN
                            (CEILING(component.product_qty / component.multiple_qty) * component.multiple_qty) * (100.0 / component.product_loss) * %(cycle)s
                    ELSE
                        component.product_qty * %(cycle)s
                    END AS res_qty
                FROM
                    mrp_bom_line component
                WHERE
                    component.id IN %(ids)s AND component.bom_id = %(bom_id)s
            ) AS res
            GROUP BY
                res.p_id
        """

    def _recursive_search_of_child_boms(self):
        children_boms = []
        for line in self.bom_line_ids:
            if line.product_id.bom_ids:
                children_boms += line.product_id.bom_ids.sorted('version', reverse=True)[0].\
                                _recursive_search_of_child_boms()
        return self.mapped('id') + children_boms
    
    @api.model
    def _bom_find(self, product_tmpl=None, product=None, picking_type=None, company_id=False, bom_type=False):
        if product and product.type != 'service' and product.bom_ids:
            if bom_type:
                lst_bom = product.bom_ids.filtered(lambda x: x.type == bom_type).sorted('version', reverse=True)
                if lst_bom:
                    return lst_bom.sorted('version', reverse=True)[0]
                return self.env['mrp.bom']
            return product.bom_ids.sorted('version', reverse=True)[0]
        
        return super(MrpBom, self)._bom_find(product_tmpl, product, picking_type, company_id, bom_type)
