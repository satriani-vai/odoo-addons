# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api

class res_partner(models.Model):
    _inherit = 'res.partner'

    min_order_sum = fields.Float('Min Order Value', default='500.0')


class sale_order(models.Model):
    _inherit = 'sale.order'

    min_order_sum_related = fields.Float(related='partner_id.min_order_sum', string='Actual Min Order Value')
    min_order_sum = fields.Float(compute='_min_order_sum_left', string='Min Order Value', store=True)
    min_order_sum_left = fields.Float(compute='_min_order_sum_left', string='Min Order Value Gap', store=True)
    min_order_sum_green = fields.Boolean('Green', default=False)

    @api.onchange('partner_id')
    def onchange_min_order_sum(self):
        for rec in self:
            if rec.state in ('draft', 'sent'):
                rec.min_order_sum = rec.min_order_sum_related

    @api.multi
    @api.depends('amount_untaxed', 'min_order_sum', 'min_order_sum_left', 'partner_id')
    def _min_order_sum_left(self):
        for rec in self:
            if rec.state in ('draft', 'sent'):
                rec.min_order_sum = rec.min_order_sum_related
            if rec.min_order_sum <= rec.amount_untaxed:
                rec.min_order_sum_left = 0.0
                rec.min_order_sum_green = True
            else:
                rec.min_order_sum_left = rec.min_order_sum - rec.amount_untaxed
                rec.min_order_sum_green = False
            if rec.amount_untaxed == 0.0:
                rec.min_order_sum_green = False
