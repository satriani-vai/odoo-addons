# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'syscoon Purchase Vendor Products',
    'version': '9.0.1.0',
    'author': 'Mathias Neef',
    'website': 'http://syscoon.com',
    'category': 'Purchase Management',
    'description': """
Sets a filter to only allow select products in purchase order, where the vendor is set.
A button in the view allows to set / remove the filter.
""",
    'depends': [
        'base',
        'purchase',
    ],
    'data': [
        'views/purchase_view.xml',
    ],
    'test':[],
    'demo': [],
    'installable': True,
    'auto_install': False,
}