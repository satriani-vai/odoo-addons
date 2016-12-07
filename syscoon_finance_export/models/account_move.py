# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, _
from openerp.exceptions import UserError
from openerp.tools.float_utils import float_is_zero

from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class AccountMove2ExportMove(models.Model):
    _inherit = 'account.move'

    move_created = fields.Boolean('Export Move Created')
    move_error = fields.Boolean('Move Error')
    move_error_message = fields.Text('Error Message')

    def st_compute_debit_credit(self, move, lines, export_config):
        overall_forward = export_config.overall_forward.code
        sum_forward = export_config.sum_forward.code
        debit_forward = export_config.debit_forward.code
        credit_forward = export_config.credit_forward.code
        wage_through = export_config.wage_through.code
        debit = 0.0
        debit_accounts = []
        credit = 0.0
        credit_accounts = []
        invoice = self.env['account.invoice'].search([('move_id', '=', move.id)])
        for line in lines:
            if line.debit:
                debit += line.debit
                debit_accounts.append(line.account_id.code)
            if line.credit:
                credit += line.credit
                credit_accounts.append(line.account_id.code)
        if overall_forward or sum_forward or debit_forward or credit_forward or wage_through in debit_accounts:
            debit_forwards = []
            if overall_forward in debit_accounts:
                debit_forwards.append(overall_forward)
            if sum_forward in debit_accounts:
                debit_forwards.append(sum_forward)
            if debit_forward in debit_accounts:
                debit_forwards.append(debit_forward)
            if credit_forward in debit_accounts:
                debit_forwards.append(credit_forward)
            if wage_through in debit_accounts:
                debit_forwards.append(wage_through)
            if debit_forwards:
                debit_accounts = []
                debit_accounts.append(debit_forwards[0])
        if overall_forward or sum_forward or debit_forward or credit_forward or wage_through in debit_accounts:
            credit_forwards = []
            if overall_forward in credit_accounts:
                credit_forwards.append(overall_forward)
            if sum_forward in credit_accounts:
                debit_accounts.append(sum_forward)
            if debit_forward in credit_accounts:
                credit_forwards.append(debit_forward)
            if credit_forward in credit_accounts:
                credit_forwards.append(credit_forward)
            if wage_through in credit_accounts:
                credit_forwards.append(wage_through)
            if credit_forwards:
                credit_accounts =[]
                credit_accounts.append(credit_forwards[0])
        if overall_forward or sum_forward or debit_forward or credit_forward or wage_through not in debit_accounts:
            if invoice and invoice.type in ['out_invoice', 'in_refund']:
                debit_accounts = []
                if not invoice.account_id.code in debit_accounts:
                    debit_accounts.append(invoice.account_id.code)
            if invoice and invoice.type in ['out_refund', 'in_invoice']:
                credit_accounts = []
                if not invoice.account_id.code in debit_accounts:
                    credit_accounts.append(invoice.account_id.code)
            for da in debit_accounts:
                account = self.env['account.account'].search([('code', '=', da)])
                if account.user_type_id.type in ('receivable', 'payable'):
                    debit_accounts =[]
                    debit_accounts.append(account.code)
            for ca in credit_accounts:
                account = self.env['account.account'].search([('code', '=', ca)])
                if account.user_type_id.type in ('receivable', 'payable'):
                    credit_accounts = []
                    credit_accounts.append(account.code)
        totals = {
            'debit': debit,
            'debit_accounts': sorted(set(debit_accounts)),
            'credit': credit,
            'credit_accounts': sorted(set(credit_accounts))
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

    def st_calculate_amount(self, move, line, tax_pc, account, export_config):
        overall_forward = export_config.overall_forward.code
        sum_forward = export_config.sum_forward.code
        debit_forward = export_config.debit_forward.code
        credit_forward = export_config.credit_forward.code
        amount = 0.0
        if line.debit:
            amount += line.debit
        if line.credit:
            amount += line.credit
        if tax_pc:
            if overall_forward == account['account']:
                amount = amount
            elif sum_forward == account['account']:
                amount = amount
            elif debit_forward == account['account']:
                amount = amount
            elif credit_forward == account['account']:
                amount = amount
            else:
                gross_amount = amount * (1 + (tax_pc / 100))
                tax = gross_amount - amount
                amount += tax
        amount = move.currency_id.round(amount)
        return amount

    def st_build_line(self, account, move, res, line, invoice, export_config):
        auto_account, tax_bkey, tax_pc, tax_account, tax_account_refund =\
            self.st_check_account(line)
        res['name'] = 'New'
        res['date'] = move.date
        res['currency'] = move.currency_id.name
        res['dc_sign'] = account['sign']
        res['amount'] = self.st_calculate_amount(move, line, tax_pc, account, export_config)
        if auto_account:
            res['bkey'] = ''
        else:
            res['bkey'] = tax_bkey
        res['account_offset'] = line.account_id.code
        res['slip1'] = move.name.replace(' !@#$%^&*()[]{};:,./<>?\|`~-=_+', '')
        if export_config.maturity_slip2:
            if line.date_maturity:
                if line.date_maturity[:4] < '1900':
                    res['slip2'] = ''
                else:
                    res['slip2'] = fields.Date.from_string(line.date_maturity).strftime('%Y%m%d')
            else:
                res['slip2'] = ''
        else:
            res['slip2'] = ''
        res['booking_date'] = fields.Date.from_string(move.date).strftime('%Y%m%d')
        res['account'] = account['account']
        res['cost1'] = ''
        res['cost2'] = ''
        res['cost_quant'] = ''
        res['discount'] = ''
        res['bookingtext'] = line.name
        if invoice.partner_id.vat and export_config.eu_fiscal_position == invoice.fiscal_position_id:
            res['vat_id'] = invoice.partner_id.vat
        else:
            res['vat_id'] = ''
        res['eu_tax'] = ''
        res['base_cur_amount'] = ''
        res['base_cur_code'] = ''
        res['exchange_rate'] = ''
        res['company_id'] = move.company_id.id
        res['account_move'] = move.id
        res['move_date'] = move.date
        return res

    def st_generate_account(self, move, lines, export_config):
        totals = self.st_compute_debit_credit(move, lines, export_config)
        account = False
        sign = False
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
        return "%s-%s-%s-%s-%s-%s" % (
            res['dc_sign'],
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

    def st_generate_line(self, move, tax_accounts, export_logger, export_errors, export_count, export_moves, export_config):
        booking = []
        res = {}
        move_error = 0
        log = []
        invoice = self.env['account.invoice'].search([('move_id', '=', move.id)])
        if move.amount:
            move_lines = move.line_ids
            account = self.st_generate_account(move, move_lines, export_config)
            export_count += 1
            if account['account'] == False:
                error = _('%s has no / to many different accounts in debit / credit and can not exported') % move.name
                log.append(error)
                export_logger.append(error)
                export_errors += 1
                move_error += 1
                move.write({'move_error': True, 'move_error_message': '\n'.join(log)})
                return export_errors, export_count, export_moves, export_logger
            for line in move_lines:
                if export_config.do_checks and invoice:
                    auto_account_id = self.env['export.auto.account'].search([('account_id', '=', line.account_id.id)])
                    tax_id = auto_account_id.vat_code
                    line_tax_id = self.env['account.tax'].search([('id', '=', line.tax_ids.id)])
                    if tax_id and tax_id.id != line.tax_ids.id:
                        line_tax_id = self.env['account.tax'].search([('id', '=', line.tax_ids.id)])
                        error1 = _('Tax Code "%s" of the Auto Account is not the same as Tax Code "%s" in the Account Line "%s" of Move "%s"') % (tax_id.description, line_tax_id.description, line.name, move.name)
                        log.append(error1)
                        export_logger.append(error1)
                        export_errors += 1
                        move_error +=1
                        continue
                if account['sign'] == 's' and line.debit:
                    account['sign'] = 'h'
                if account['sign'] == 'h' and line.credit:
                    account['sign'] = 's'
                res = self.st_build_line(account, move, res, line, invoice, export_config)
                if res['account_offset'] != res['account']:
                    if res['account_offset'] in tax_accounts:
                        continue
                    elif res['account'] in tax_accounts:
                        continue
                    else:
                        booking.append(res.copy())
                        export_moves += 1
            if not booking:
                move_error += 1
                export_errors += 1
                error2 = _('Move %s can not be exported, because it is empty.') % (move.name)
                log.append(error2)
                export_logger.append(error2)
            grouped_lines = self.st_create_group(booking)
            """
            amount_check_s = 0.0
            amount_check_h = 0.0
            for gl in grouped_lines:
                if gl['dc_sign'] == 's':
                    amount_check_s += gl['amount']
                if gl['dc_sign'] == 'h':
                    amount_check_h += gl['amount']
            if amount_check_h > amount_check_s:
                amount_check = amount_check_h - amount_check_s
            else:
                amount_check = amount_check_s - amount_check_h
            amch = round(move.amount - amount_check, 2)
            if amch != 0.0:
                move_error += 1
                export_errors += 1
                error2 = _('Move %s can not be exported, because Amount %s in Export-Move is not equal to the Amount %s in Move') % (move.name, amount_check, move.amount)
                log.append(error2)
                export_logger.append(error2)
            """
            if move_error == 0:
                for gl in grouped_lines:
                    if move_error == 0:
                        self.env['export.move'].create(gl)
                        move.write({'move_created': True})
            if move_error != 0:
                move.write({'move_error': True, 'move_error_message': '\n'.join(log)})
            return export_errors, export_count, export_moves, export_logger


    def st_check_tax_lines(self):
        tax_accounts = []
        for txid in self.env['account.tax'].search([]):
            if txid.account_id and txid.account_id.code not in tax_accounts:
                tax_accounts.append(txid.account_id.code[:4])
            if txid.refund_account_id and txid.refund_account_id.code not in tax_accounts:
                tax_accounts.append(txid.refund_account_id.code[:4])
        return tax_accounts

    @api.multi
    def action_export_move_create(self):
        export_logger = []
        export_errors = 0
        export_count = 0
        export_moves = 0
        tax_accounts = self.st_check_tax_lines()
        company = self.env['res.company']._company_default_get('account.move')
        export_config = self.env['export.configuration'].search([('company_id', '=', company.id)])
        for move in self:
            if not move.amount:
                export_logger.append(_('%s has amount 0,00 and can not exported') % move.name)
                export_errors += 1
            else:
                em = self.st_generate_line(move, tax_accounts, export_logger, export_errors, export_count, export_moves, export_config)
                export_moves = em[2]
                export_count = em[1]
                export_errors = em[0]
                export_logger = em[3]
                _logger.info('Move %s created.', move.name)
        if not export_errors:
            export_logger.append(_('No Errors, %d moves correctly created') % export_moves)
        self.env['export.logger'].create({
            'name': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'errors': export_errors,
            'counts': export_count,
            'moves': export_moves,
            'logging': '\n'.join(export_logger)
        })

    @api.multi
    def button_cancel(self):
        for move in self:
            if move.move_created == True:
                raise UserError(_('Forbidden to Cancel! You can not delete a Move which is exported! Please delete the Datev-Export first'))
        return super(AccountMove2ExportMove, self).button_cancel()

    @api.model
    def create(self, vals):
        move = super(AccountMove2ExportMove, self).create(vals)
        company = self.env['res.company']._company_default_get('account.move')
        export_config = self.env['export.configuration'].search([('company_id', '=', company.id)])
        if export_config.do_checks:
            for line in vals['line_ids']:
                auto_account_id = self.env['export.auto.account'].search([('account_id', '=', line[2]['account_id'])])
                tax_id = auto_account_id.vat_code
                if tax_id and tax_id.id != line[2]['tax_ids'][0][1]:
                    line_tax_id = self.env['account.tax'].search([('id', '=', line[2]['tax_ids'][0][1])])
                    raise UserError(_('Tax Code "%s" of the Auto Account is not the same as Tax Code "%s" in the Account Line') % (tax_id.description, line_tax_id.description))
        return move
