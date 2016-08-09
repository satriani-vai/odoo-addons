# -*- coding: utf-8 -*-
# This file is part of syscoon. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
################################################################################

from openerp import models, fields, api, _

class res_partner(models.Model):
    _inherit = 'res.partner'

    partner_salutation = fields.Char(compute='_compute_salutation', string='Salutation')

    @api.model
    @api.depends('title')
    def _compute_salutation(self):
        for ps in self:
            if ps.title:
                if ps.title.name_selection == 'complete':
                    salname = '%s %s' % (ps.firstname, ps.lastname)
                elif ps.title.name_selection == 'lastname':
                    salname = ps.lastname
                elif ps.title.name_selection == 'firstname':
                    salname = ps.firstname
                ps.partner_salutation = '%s %s' % (ps.title.salutation, salname)
            else:
                ps.partner_salutation = _('Dear Sir or Madam')


class res_partner_title(models.Model):
    _inherit = 'res.partner.title'

    NAME_SELECT = [
        ('complete', 'Complete Name'),
        ('lastname', 'Lastname'),
        ('firstname', 'Firstname'),
        ('none', 'None'),
    ]

    name_selection = fields.Selection(NAME_SELECT, 'Name Selection', default='complete')
    salutation = fields.Char('Salutation', translate=True)

