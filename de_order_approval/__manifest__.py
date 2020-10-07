# -*- coding: utf-8 -*-
{
    'name': "Sale Order Approval",

    'summary': """
        Sale Order Approval
        """,

    'description': """
    Sale Order Approval
    =========================
        Sale Order Approval- Only users with particular group access will be able to approve the order.
    """,

    'author': "Dynexcel",
    'website': "http://www.dynexcel.com",
    "live_test_url": "https://youtu.be/tNrBIrCzPPQ",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'sale',
    'version': '0.5',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'security/security.xml',
        'views/sale_views.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    "images":  ['static/description/banner.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
