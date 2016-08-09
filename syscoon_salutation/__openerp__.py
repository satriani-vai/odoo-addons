# -*- coding: utf-8 -*-
# This file is part of syscoon. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
################################################################################

{
    'name': 'syscoon Salutation',
    'version': '9.0.1.0',
    'category': 'Administration',
    'author': 'Mathias Neef',
    'website': 'https://syscoon.com',
    'depends': [
        'base',
        'partner_firstname',
    ],
    'data': [
        'views/res_partner_salutation.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}
