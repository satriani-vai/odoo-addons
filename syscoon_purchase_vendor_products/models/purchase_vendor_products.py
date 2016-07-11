# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    product_filter = fields.Boolean('Product Filter', default=True)

    @api.multi
    def action_set_product_filter(self):
        self.ensure_one()
        if self.product_filter:
            self.product_filter = False
        else:
            self.product_filter = True
        return


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()

        supplier_infos = self.env['product.supplierinfo'].search([('name', '=', self.partner_id.id)])
        product_ids = self.env['product.product']
        for supplier_info in supplier_infos:
            product_ids += supplier_info.product_tmpl_id.product_variant_ids
        if self.order_id.product_filter:
            result.update({'domain': {'product_id': [('id', 'in', product_ids.ids)]}})

        return result
