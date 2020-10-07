from datetime import datetime

import requests
from odoo.exceptions import ValidationError

from odoo import models, fields, api
from custom_addons.odoo_mpesa.controllers.mpesa_credentials import ShortcodeInstanceCredentials


class ShortCodeInstance(models.Model):
    _name = "odoo_mpesa.configuration"
    _description = "Mpesa ShortCode Configuration"

    shortcode = fields.Integer(required=True, string="ShortCode", unique=True)
    type = fields.Selection([('till', 'Till Number'), ('paybill', 'PayBill Number')], 'Type', default='till')
    initiator = fields.Char(required=True, string="Initiator Name")
    security_credential = fields.Char(required=True, string="Security Credential")
    pass_key = fields.Char(required=True, string="Pass Key")
    consumer_key = fields.Char(required=True, string="Consumer Key")
    consumer_secret = fields.Char(required=True, string="Consumer Secret")
    active = fields.Boolean(string="Active status", default=True)

    @api.model
    def create(self, vals, *args, **kwargs):
        credentials = ShortcodeInstanceCredentials(vals)
        if not credentials.register_urls():
            raise ValidationError("We could not verify the provided credentials.")
        return super(ShortCodeInstance, self).create(vals, *args, **kwargs)

    def write(self, values):
        configuration = {"shortcode": self.shortcode,
                         "pass_key": self.pass_key,
                         "consumer_key": self.consumer_key,
                         "consumer_secret": self.consumer_secret,
                         "initiator": self.initiator,
                         "type": self.type,
                         "security_credential": self.security_credential,
                         }
        configuration.update(values)
        credentials = ShortcodeInstanceCredentials(configuration)
        if not credentials.register_urls():
            raise ValidationError("We could not verify the provided credentials")
        return super(ShortCodeInstance, self).write(values)


class MpaymentRecord(models.Model):
    _name = "odoo_mpesa.record"
    _description = "Mpesa Payment Records"

    transaction_id = fields.Char(string="Transaction ID", unique=True)
    customer = fields.Char()
    amount = fields.Float(string="Amount (Ksh)")
    phone_number = fields.Char()
    type = fields.Char()
    reference = fields.Char()
    configuration = fields.Many2one(comodel_name="odoo_mpesa.configuration", string="Shortcode used", required=True,
                                    ondelete="restrict", delegate=True, auto_join=True)


class TransactionStatus(models.Model):
    _name = "odoo_mpesa.status"
    _description = "Mpesa Transaction Status"

    transaction_id = fields.Char(required=True, unique=True)
    result_code = fields.Integer(required=True)
    description = fields.Text()
    customer = fields.Char()
    amount = fields.Float()
