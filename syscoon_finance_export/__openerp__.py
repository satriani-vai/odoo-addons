# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'copadoMEDIA Datev-Export',
    'version': '9.0.0.1',
    'category': 'Sales',
    'author': 'Mathias Neef',
    'description': """
Generates a CSV-Export for Datev.
    """,
    'website': 'http://copado.de',
    'depends' : ['account'],
    'data': [
        'data/sequences.xml',
        'views/menu.xml',
        'views/key.xml',
        'views/auto_account.xml',
        'views/move.xml',
        'views/configuration.xml',
        'views/exports.xml',
        'wizard/move_create_view.xml',
        'wizard/move_unlink_view.xml',
        'wizard/move_export_view.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}