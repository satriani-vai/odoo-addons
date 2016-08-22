# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import cStringIO
import csv
import base64
import datetime

from openerp import models, fields, api, _
from openerp.exceptions import UserError

class ExportMove(models.Model):
    _name = 'export.move'
    _order = 'name desc, move_date'

    name = fields.Char('Name', default='New')
    date = fields.Char('Date')
    state = fields.Selection([('created', 'Created'),
        ('exported', 'Exported')],
        string='Status', required=True,
        readonly=True, default='created')
    currency = fields.Char('Currency', size=3)
    dc_sign = fields.Char('Debit / Credit Sign', size=1)
    amount = fields.Char('Amount', size=30)
    bkey = fields.Char('Booking Key', size=2)
    account_offset = fields.Char('Offset Account', size=8)
    slip1 = fields.Char('Slip Field 1', size=12)
    slip2 = fields.Char('Slip Field 2', size=6)
    booking_date = fields.Char('Date', size=4)
    account = fields.Char('Account', size=8)
    cost1 = fields.Char('Cost 1', size=30)
    cost2 = fields.Char('Cost 2', size=30)
    cost_quant = fields.Char('Cost Quantity', size=30)
    discount = fields.Char('Discount', size=30)
    bookingtext = fields.Char('Booking Text', size=60)
    vat_id = fields.Char('VAT-ID', size=30)
    eu_tax = fields.Char('EU Tax Rate', size=10)
    base_cur_amount = fields.Char('Base Currency Amount', size=30)
    base_cur_code = fields.Char('Base Currency Code', size=3)
    exchange_rate = fields.Char('Currency Exchange Rate', size=30)
    company_id = fields.Many2one('res.company',
        string='Company', required=True, 
        default=lambda self: self.env['res.company'].\
        _company_default_get('datev.auto.account'))
    export_export = fields.Many2one('export.exports', string='Export')
    account_move = fields.Many2one('account.move', string="Account Move")
    move_date = fields.Date('Move Date')

    def _create_date_range(self, dates):
        min_date = min(dates)
        max_date = max(dates)
        return '%s - %s' % (min_date, max_date)

    def _check_moves(self, moves_2_check, export_moves):
        export_moves_check = export_moves
        for m2d in moves_2_check:
            if m2d not in export_moves:
                export_moves_check += m2d
        if export_moves_check == export_moves:
            return export_moves
        else:
            return export_moves_check

    #todo: select all export-moves from odoo-move
    @api.multi
    def action_create_export_file(self):
        export_id = self.env['export.exports'].create({'name': 'New', 'state': 'draft'})
        export_moves = self.env['export.move']
        for m in self:
            if m.state == 'created':
                moves_2_check = self.env['export.move'].search([('account_move', '=', m.account_move.id)])
                export_moves = self._check_moves(moves_2_check, export_moves)
        csv_buffer = cStringIO.StringIO()
        writer = csv.writer(csv_buffer, delimiter=';', quotechar='"')
        company = self.env['res.company'].\
            _company_default_get('export.exports')
        export_config = self.env['export.configuration'].\
            search([('company_id', '=', company.id)])
        export_header = [
            'Währungskennung', 'Soll-/Haben-Kennzeichen',
            'Umsatz (ohne Soll-/Haben-Kennzeichen)', 'BU-Schlüssel',
            'Gegenkonto (ohne BU-Schlüssel)', 'Belegfeld 1', 'Belegfeld 2',
            'Datum', 'Konto', 'Kostfeld 1', 'Kostfeld 2', 'Kostmenge',
            'Skonto', 'Buchungstext', 'EU-Land und UStID', 'EU-Steuersatz',
            'Basiswährungsbetrag', 'Basiswährungskennung', 'Kurs'
        ]
        writer.writerow(export_header)
        dates = []
        for e in export_moves:
            dates.append(e.move_date)
            export_row = [e.currency, e.dc_sign, e.amount, e.bkey, e.account_offset,
                e.slip1, e.slip2, e.booking_date, e.account, e.cost1, e.cost2, e.cost_quant,
                e.discount, e.bookingtext, e.vat_id, e.eu_tax, e.base_cur_amount,
                e.base_cur_code, e.exchange_rate
            ]
            writer.writerow(export_row)
            e.write({'state': 'exported', 'export_export': export_id.id})
        export_val = {
            'state': 'created',
            'date_range': self._create_date_range(dates),
            'file': base64.encodestring(csv_buffer.getvalue()),
            'company_id': company.id,
            'note': '%s Moves exported' % len(export_moves)
        }
        export_id.write(export_val)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].\
            next_by_code('st.export.move.sequence')
        return super(ExportMove, self).create(vals)

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        raise UserError(_('Forbbiden to duplicate!'),\
            _('Is not possible to duplicate a Datev Move!'))

    @api.multi
    def action_datev_move_unlink(self):
        account_moves = self.env['account.move']
        export_moves = self.env['export.move']
        for dm in self:
            moves_2_check = self.env['export.move'].search([('account_move', '=', dm.account_move.id)])
            export_moves = self._check_moves(moves_2_check, export_moves)
            if dm.account_move not in account_moves:
                account_moves += dm.account_move
        for move in export_moves:
            move.unlink()
        account_moves.write({'state': 'posted'})
