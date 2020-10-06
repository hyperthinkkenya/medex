# -*- coding: utf-8 -*-
# from odoo import http


# class DeApprovalState(http.Controller):
#     @http.route('/de_approval_state/de_approval_state/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/de_approval_state/de_approval_state/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('de_approval_state.listing', {
#             'root': '/de_approval_state/de_approval_state',
#             'objects': http.request.env['de_approval_state.de_approval_state'].search([]),
#         })

#     @http.route('/de_approval_state/de_approval_state/objects/<model("de_approval_state.de_approval_state"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('de_approval_state.object', {
#             'object': obj
#         })
