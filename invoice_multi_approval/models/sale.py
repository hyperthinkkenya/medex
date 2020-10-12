from odoo import models

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()   
        
        approver_lines = []
        invoice_approval_ids = self.env['invoice.approval'].search(
            []).mapped('invoice_approver_ids')

        for ids in invoice_approval_ids:
            val = {'approver_id': ids}
            approver_lines.append((0, 0, val))
        invoice_vals['approval_ids'] = approver_lines
        return invoice_vals

      