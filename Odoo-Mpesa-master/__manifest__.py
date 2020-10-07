# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Mpesa Paybill/Till',
    'version': '1.1',
    'summary': 'Mpesa Payment for Odoo POS',
    'sequence': 10,
    'author': "John Gaitho",
    'description': """
Invoicing & Payments
====================
    An extension to Odoo POS to allow for payment via Mpesa
    """,
    'category': 'Sales/Point Of Sale',
    'website': 'https://www.odoo.com/page/hospital',
    'images': [],
    'depends': ['point_of_sale'],
    'data': [
        'views/mpayment_view.xml',
        'views/mpayment_validation_view.xml',
        'security/ir.model.access.csv',
        'views/test.xml'
    ],
    'demo': [
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
