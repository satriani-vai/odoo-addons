# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'syscoon Minimum Sale-Order Value',
    'version': '9.0.1.0',
    'author': 'Mathias Neef',
    'website': 'http://syscoon.com',
    'category': 'Sales Management',
    'description': """
Displays a simple minimum Sale-Order value and the remaining value in each Sale Order, based on the settings in the Partner.
It only shows the remaining value, but does not prevent from confirmating the order.
""",
    'depends': [
        'base',
        'sale',
    ],
    'data': [
        'views/min_order_value.xml',
    ],
    'test':[],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
