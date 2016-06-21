# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp.tools.float_utils import float_is_zero


class AccountMove2ExportMove(models.Model):
    _inherit = 'account.move'

    state = fields.Selection(
        selection_add=[('export_move', 'Datev Move Created')])

    def st_compute_debit_credit(self, lines):
        debit = 0.0
        debit_accounts = []
        credit = 0.0
        credit_accounts = []
        for line in lines:
            if line.debit:
                debit += line.debit
                debit_accounts.append(line.account_id.code)
            if line.credit:
                credit += line.credit
                credit_accounts.append(line.account_id.code)
        totals = {
            'debit': debit,
            'debit_accounts': debit_accounts,
            'credit': credit,
            'credit_accounts': credit_accounts
        }
        return totals

    def st_create_tax_additions(self, line):
        tax_bkey, tax_pc, tax_account, tax_account_refund = '', 0.0, '', ''
        if line.tax_ids and len(line.tax_ids) == 1:
            tax = self.env['export.key'].search(
                [('vat_code', '=', line.tax_ids.id)], limit=1)
            tax_bkey = tax.export_key
            tax_pc = tax.vat_code.amount
            tax_account = tax.vat_code.account_id.code
            tax_account_refund = tax.vat_code.refund_account_id.code
        return tax_bkey, tax_pc, tax_account, tax_account_refund

    def st_check_account(self, line):
        auto_account_id = self.env['export.auto.account'].search(
            [('account_id', '=', line.account_id.id)])
        tax_bkey, tax_pc, tax_account, tax_account_refund =\
            self.st_create_tax_additions(line)
        if auto_account_id:
            if float_is_zero(tax_pc, precision_rounding=2):
                tax_pc = auto_account_id.vat_code.amount
        return bool(auto_account_id), tax_bkey, tax_pc, tax_account, tax_account_refund

    def st_calculate_amount(self, move, line, tax_pc):
        #todo: gross if company-settings are gross
        amount = 0.0
        if line.debit:
            amount += line.debit
        if line.credit:
            amount += line.credit
        if tax_pc:
            gross_amount = amount * (1 + (tax_pc / 100))
            tax = gross_amount - amount
            amount += tax
        amount = move.currency_id.round(amount)
        amount = str(amount).replace('.', ',')
        return amount

    def st_build_line(self, account, move, res, line):
        auto_account, tax_bkey, tax_pc, tax_account, tax_account_refund =\
            self.st_check_account(line)
        res['name'] = 'New'
        res['date'] = move.date
        res['currency'] = move.currency_id.name
        res['dc_sign'] = account['sign']
        res['amount'] = self.st_calculate_amount(move, line, tax_pc)
        if auto_account:
            res['bkey'] = ''
        else:
            res['bkey'] = tax_bkey
        res['account_offset'] = line.account_id.code
        res['slip1'] = move.name.replace('/', '')
        if line.date_maturity:
            res['slip2'] = fields.Date.from_string(line.date_maturity).strftime('%d%m%y')
        else:
            res['slip2'] = ''
        res['booking_date'] = fields.Date.from_string(move.date).strftime('%d%m')
        res['account'] = account['account']
        res['cost1'] = ''
        res['cost2'] = ''
        res['cost_quant'] = ''
        res['discount'] = ''
        res['bookingtext'] = line.name
        res['vat_id'] = ''
        res['eu_tax'] = ''
        res['base_cur_amount'] = ''
        res['base_cur_code'] = ''
        res['exchange_rate'] = ''
        res['company_id'] = move.company_id.id
        res['account_move'] = move.id
        res['move_date'] = move.date
        return res

    def st_generate_account(self, lines):
        totals = self.st_compute_debit_credit(lines)
        for line in lines:
            if len(totals['debit_accounts']) == 1 and not line.tax_ids:
                account = totals['debit_accounts'][0]
                sign = 's'
            if len(totals['credit_accounts']) == 1 and not line.tax_ids:
                account = totals['credit_accounts'][0]
                sign = 'h'
        return {
            'account': account,
            'sign': sign
        }

    def st_generate_hash(self, res):
        return "%s-%s-%s-%s-%s" % (
            res.get('bkey', 'False'),
            res['account'], 
            res['account_offset'],
            res.get('cost1', 'False'),
            res.get('cost2', 'False')
        )

    def st_create_group(self, booking):
        line2 = {}
        for b in booking:
            tmp = self.st_generate_hash(b)
            if tmp in line2:
                am = line2[tmp]['amount'] + b['amount']
                bt = line2[tmp]['bookingtext'] + ' ' + b['bookingtext']
                line2[tmp]['amount'] = am
                line2[tmp]['bookingtext'] = bt
            else:
                line2[tmp] = b
        booking = []
        for key, val in line2.items():
            booking.append(val.copy())
        return booking

    def st_generate_line(self, move, tax_accounts):
        booking = []
        res = {}
        move_lines = move.line_ids
        #move_lines = self.env['account.move.line'].search([('move_id', '=', move.id)])
        account = self.st_generate_account(move_lines)
        for line in move_lines:
            res = self.st_build_line(account, move, res, line)
            if res['account_offset'] != res['account']:
                if res['account_offset'] in tax_accounts:
                    continue
                elif res['account'] in tax_accounts:
                    continue
                else:
                    booking.append(res.copy())
        grouped_lines = self.st_create_group(booking)
        for gl in grouped_lines:
            self.env['export.move'].create(gl)
            self.write({'state': 'export_move'})

    def st_check_tax_lines(self):
        tax_accounts = []
        for txid in self.env['account.tax'].search([]):
            if txid.account_id and txid.account_id.code not in tax_accounts:
                tax_accounts.append(txid.account_id.code)
            if txid.refund_account_id and txid.refund_account_id.code not in tax_accounts:
                tax_accounts.append(txid.refund_account_id.code)
        return tax_accounts

    @api.multi
    def action_export_move_create(self):
        tax_accounts = self.st_check_tax_lines()
        company = self.env['res.company']._company_default_get('account.move')
        # export_config will be used in a later version
        export_config = self.env['export.configuration'].search([('company_id', '=', company.id)])
        for move in self:
            self.st_generate_line(move, tax_accounts)

    @api.multi
    def button_cancel(self):
        for move in self:
            if move.state == 'export_move':
                raise UserError(_('Forbidden to Cancel!'),\
                    _('You can not delete a Move which is exported to Datev!'),\
                    _('Please delete the Datev-Export first'))
        return super(AccountMove2ExportMove, self).button_cancel()
