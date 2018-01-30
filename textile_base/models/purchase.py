# -*- coding: utf-8 -*-
# © 2017 Comunitea Servicios Tecnológicos S.L. (http://comunitea.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api
from odoo import tools


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_id')
    def _get_color(self):
        for pol in self:
            colors = pol.product_id.attribute_value_ids.filtered('is_color')
            pol.color_id = colors[0] if colors else False

    color_id = fields.Many2one('product.attribute.value',
                               compute='_get_color', store=True)
    line_note = fields.Text('Line Note')


class GroupPoLine(models.Model):
    _name = "group.po.line"
    _auto = True
    _description = "Groping Purchase Order Lines"

    id = fields.Integer('Id', readonly=True)
    template_id = fields.Many2one('product.template', 'Template',
                                  readonly=True)
    att_detail = fields.Text('Attribute Detail', readonly=True,
                             compute='_get_detail')
    order_id = fields.Many2one('purchase.order', 'Order', readonly=True)
    color_id = fields.Many2one('product.attribute.value', readonly=True)
    width = fields.Float('Width', readonly=True)
    grammage = fields.Float('Grammage', readonly=True)
    gauge = fields.Float('Gauge', readonly=True)
    thread = fields.Float('thread', readonly=True)
    qty = fields.Float('Qty', readonly=True)
    price = fields.Float('Price', readonly=True)

    @api.multi
    def _get_lines_ungruped(self):
        import ipdb; ipdb.set_trace()
        self.ensure_one()
        res = self.env['purchase.order.line']
        for line in self.order_id.order_line:
            if line.color_id.id == self.color_id.id and \
                    line.product_id.product_tmpl_id.id == self.template_id.id:
                res += line
        return res

    @api.model
    def _get_att_detail_str(self, gpl, detail_dic):
        separator = '  '
        res = ""
        line1_str = ""
        line2_str = ""
        for v_name in detail_dic:
            value_str = str(detail_dic[v_name])
            len1 = len(v_name)
            len2 = len(value_str)
            max_len = max(len1, len2) + len(separator)
            sepa1 = ''
            for i in range(0, max_len - len1):
                sepa1 += ' '
            sepa2 = ''
            for i in range(0, max_len - len2):
                sepa2 += ' '
            line1_str += v_name + sepa1
            line2_str += value_str + sepa2

        if line1_str and line2_str:
            res = line1_str + '\n' + line2_str
        return res

    @api.multi
    def _get_detail(self):
        for gpl in self:
            detail_dic = {}
            for pol in gpl._get_lines_ungruped():
                size_att = pol.product_id.attribute_value_ids.\
                    filtered(lambda v: v.is_color is False)
                if size_att:
                    detail_dic[size_att.name] = pol.product_qty

            self.att_detail = self._get_att_detail_str(gpl, detail_dic)

    @api.model_cr
    def init(self):
        """
        @param cr: the current row, from the database cursor
        """
        tools.drop_view_if_exists(self._cr, 'group_po_line')
        self._cr.execute("""
CREATE OR REPLACE VIEW group_po_line AS (
SELECT
min(pol.id) as id,
pp.product_tmpl_id AS template_id,
pol.order_id AS order_id,
pol.color_id AS color_id,
sum(pol.width) as width,
sum(pol.grammage) as grammage,
sum(pt.gauge) as gauge,
sum(pt.thread) as thread,
sum(pol.product_qty) AS qty,
sum(pol.price_unit) AS price
FROM purchase_order_line pol
LEFT JOIN product_product pp ON pp.id = pol.product_id
LEFT JOIN product_template pt on pt.id = pp.product_tmpl_id
GROUP BY pol.order_id, pp.product_tmpl_id, pol.color_id
)""")


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('product_id')
    def _get_color(self):
        for pol in self:
            colors = pol.product_id.attribute_value_ids.filtered('is_color')
            pol.color_id = colors[0] if colors else False

    grouped_line_ids = fields.One2many('group.po.line', 'order_id',
                                       'Grouped Lines')
    line_note = fields.Text('Line Note')