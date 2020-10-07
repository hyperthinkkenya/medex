# -*- coding: utf-8 -*-
import asyncio
import json
import aiohttp
import requests

from odoo import http
from odoo.http import request
from .mpesa_credentials import ShortcodeInstanceCredentials, HOST


class MPaymentController(http.Controller):

    def get_transaction(self, seach_dict):
        mpayment_records = request.env['odoo_mpesa.record'].sudo()
        filtered_records = mpayment_records.search([(key, '=', value) for key, value in seach_dict.items()], limit=1)
        return filtered_records[0] if filtered_records else None

    def get_configuration(self, seach_dict):
        configurations = request.env['odoo_mpesa.configuration'].sudo()
        configurations = configurations.search([(key, '=', value) for key, value in seach_dict.items()], limit=1)
        return configurations[0] if configurations else None

    def customized_message(self, ref):
        transaction = self.get_transaction({"reference": ref})
        message = f"{transaction.transaction_id} >> {transaction.customer} >> {transaction.phone_number}" \
                  f" >> Sh.{transaction.amount} >> {transaction.reference}"
        return message

    def transaction_type_verbose(self, trans_type):
        return "Pay Bill" if "bill" in trans_type.lower() else "Buy Goods"

    def get_transaction_type(self, shortcode):
        configuration = self.get_configuration({"shortcode": int(shortcode)})
        return self.transaction_type_verbose(configuration.type) if configuration else ""

    def get_transaction_status(self, search_dict):
        records = request.env['odoo_mpesa.status'].sudo()
        filtered_records = records.search([(key, '=', value) for key, value in search_dict.items()], limit=1)
        return filtered_records[0] if filtered_records else None

    def get_transaction_status_message(self, trans_id, ref):
        status = self.get_transaction_status({"transaction_id": trans_id})
        if status:
            message = f'{status.transaction_id} >>{status.customer} >> {status.amount}'
            number = status.customer.split(" - ")[0]
            if self.number_is_correct(number):
                order_details = {
                    "amount": status.amount,
                    "phone": self.formatted_number(number),
                    "ref": ref
                }
                self.run_simulation(order_details)
            return message
        return

    def number_is_correct(self, number):
        if number[0] == '+':
            number = number[1:]
        try:
            print(int(number))
            if number[0] == '0' and len(number) == 10 or number[0] == '7' and \
                    len(number) == 9 or number[0:3] == '254' and len(number) == 12:
                return True
            else:
                return False
        except ValueError:
            return False

        # converting the phone number in to the required format before sending mpesa simulate request

    def formatted_number(self, number):
        if number[0] == '+':
            number = number[1:]
        elif number[0] == '0':
            number = '254' + number[1:]
        elif number[0] == '7':
            number = '254' + number
        return int(number)

    def update_transaction_status(self, data):
        record = request.env['odoo_mpesa.status'].sudo().search([])
        trans_status = self.get_transaction_status({"transaction_id": data["transaction_id"]})
        if not trans_status:
            record.create(data)

    def record_transaction(self, data):
        if not self.get_transaction({'reference': data['reference']}):
            records = request.env['odoo_mpesa.record'].sudo().search([])
            records.create(data)

    def get_configurations(self):
        return request.env['odoo_mpesa.configuration'].sudo().search([("active", "=", True)])

    def record_reversal(self, response_data, original_transaction):
        configuration = self.get_configuration({"shortcode": original_transaction['shortcode']})
        data = {
            "type": "Reversal",
            "customer": original_transaction["first_name"] + " " + original_transaction["last_name"],
            "transaction_id": response_data["TransactionID"],
            "phone_number": original_transaction["phone_number"],
            "amount": -response_data['Amount'],
            "reference": response_data["OriginalTransactionID"],
            "configuration": configuration.id
        }
        self.record_transaction(data)

    @http.route('/lipa/timeout', type='json', auth='user', website=True)
    def reversal_timeout(self):
        response = json.loads(request.httprequest.data)
        print("Request timeout", response)

    @http.route('/lipa/reversal/result', type='json', auth='public', website=True)
    def handle_reversal_response(self):
        response = json.loads(request.httprequest.data)["Result"]
        code = response["ResultCode"]
        if code == 0:
            try:
                raw_data = response["ResultParameters"]["ResultParameter"]
                refined = {}
                for obj in raw_data:
                    try:
                        refined.update({obj["Key"]: obj["Value"]})
                    except KeyError:
                        pass
                original_id = refined["OriginalTransactionID"]
                transaction = self.get_transaction({"transaction_id": original_id})
                if transaction:
                    self.record_reversal(refined, transaction)
            except:
                print("Reversal was processed successfully  but could not be recorded locally")
        else:
            print(response)

    def record_payment(self, mpayment_data):
        shortcode = mpayment_data['BusinessShortCode']
        configuration = self.get_configuration({"shortcode": shortcode})
        data = {
            "type": mpayment_data["TransactionType"] or self.get_transaction_type(shortcode),
            "customer": mpayment_data['FirstName'] + " " + mpayment_data['LastName'],
            "transaction_id": mpayment_data['TransID'],
            "phone_number": mpayment_data['MSISDN'],
            "amount": float(mpayment_data['TransAmount']),
            "reference": mpayment_data['BillRefNumber'],
            "configuration": configuration.id
        }
        self.record_transaction(data)

    async def send_simulate_request(self, session, configuration, order_details):
        credentials = ShortcodeInstanceCredentials(configuration)
        api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/simulate"
        headers = {"Authorization": "Bearer %s" % credentials.access_token()}
        to_request = {"ShortCode": credentials.shortcode,
                      "CommandID": "CustomerPayBillOnline",
                      "Amount": order_details["amount"],
                      "Msisdn": order_details["phone"],
                      "BillRefNumber": order_details["ref"]
                      }
        async with session.post(api_url, json=to_request, headers=headers) as response:
            print(response)

    async def handle_concurrency(self, order_details):
        configurations = self.get_configurations()
        async with aiohttp.ClientSession() as session:
            tasks = []
            for configuration in configurations:
                task = asyncio.ensure_future(self.send_simulate_request(session, configuration, order_details))
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=True)

    def run_simulation(self, order_details):
        asyncio.run(self.handle_concurrency(order_details))

    async def send_status_request(self, session, configuration, trans_id, indentifier):
        credentials = ShortcodeInstanceCredentials(configuration)
        api_url = "https://sandbox.safaricom.co.ke/mpesa/transactionstatus/v1/query"
        headers = {"Authorization": "Bearer %s" % credentials.access_token()}
        to_request = {
            "Initiator": credentials.initiator,
            "SecurityCredential": credentials.security_credential,
            "CommandID": "TransactionStatusQuery",
            "TransactionID": trans_id,
            "PartyA": credentials.shortcode,
            "IdentifierType": indentifier,
            "ResultURL": HOST + "/lipa/status/result",
            "QueueTimeOutURL": HOST + "/timeout",
            "Remarks": "Transaction status",
            "Occasion": "Odoo POS"
        }
        async with session.post(api_url, json=to_request, headers=headers) as response:
            print(response)

    async def request_status(self, trans_id, indentifier):
        configurations = self.get_configurations()
        async with aiohttp.ClientSession() as session:
            tasks = []
            for configuration in configurations:
                task = asyncio.ensure_future(self.send_status_request(session, configuration, trans_id, indentifier))
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=True)

    def run_status_request(self, trans_id, indentifier):
        asyncio.run(self.request_status(trans_id, indentifier))

    @http.route('/lipa/confirm', type='json', auth='public', website=True)
    def confirm_payment(self):
        mpayment_data = json.loads(request.httprequest.data)
        self.record_payment(mpayment_data)
        return {
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        }

    @http.route('/lipa/validate', type='json', auth='public', website=True)
    def validate_payment(self):
        data = json.loads(request.httprequest.data)
        self.record_payment(data)
        return {
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        }

    @http.route('/lipa/status/result', type='json', auth='public', website=True)
    def handle_status_response(self):
        response = json.loads(request.httprequest.data)["Result"]
        code = response["ResultCode"]
        description = response["ResultDesc"]
        if code == 0:
            raw_data = response["ResultParameters"]["ResultParameter"]
            refined = {}
            for obj in raw_data:
                try:
                    refined.update({obj["Key"]: obj["Value"]})
                except KeyError:
                    pass

            data = {
                "result_code": code,
                "description": description,
                "transaction_id": refined["ReceiptNo"],
                "amount": refined["Amount"],
                "customer": refined["DebitPartyName"]

            }
            self.update_transaction_status(data)

        else:
            print(response)

    @http.route('/lipa/simulate', type='json', auth='public', methods=['POST'], website=True)
    def simulate_payment(self, **kwargs):
        configurations = self.get_configurations()
        shortcodes_count = configurations.search_count([])
        if shortcodes_count == 0:
            return {'message': "It seems like you don't have an active shortcode configured",
                    'code': 1}
        amount = kwargs.get("amount", False)
        ref = kwargs.get("ref", False)
        trans_id = kwargs.get("trans_id", False)
        indentifier = kwargs.get("indentifier")

        if amount and ref and trans_id:
            if self.get_transaction({'reference': ref}):
                return {'message': self.customized_message(ref), 'code': 0}
            if not self.number_is_correct(trans_id):
                return self.check_transaction_status(trans_id, indentifier)
            phone = self.formatted_number(trans_id)
            order_details = {
                "amount": amount,
                "phone": phone,
                "ref": ref
            }
            status_message = self.get_transaction_status_message(trans_id, ref)
            if status_message:
                return {"message": status_message, "code": 0}
            self.run_simulation(order_details)
            return {"message": "Processing Request", "code": -1}
        return {'message': 'Server Error: Some required inputs are missing', 'code': 1}

    @http.route('/lipa/reversal', type='json', auth='public', methods=['POST'], website=True)
    def reverse_payment(self, **kwargs):
        transaction_id = kwargs.get("transaction_id", False)
        order = kwargs.get("order", False)
        if self.get_transaction({"reference": f'{transaction_id}, {order}'}):
            ref = f'{transaction_id}, {order}'
            return {"message": self.customized_message(ref), "code": 0}
        if self.get_transaction({"reference": transaction_id}):
            return {"message": self.customized_message(transaction_id), "code": 0}
        amount = kwargs.get("amount", False)
        receiver_type = kwargs.get("receiver_type")
        if not transaction_id:
            return {'message': 'Transaction ID is required to process reversal', 'code': 1}
        transaction = self.get_transaction({'transaction_id': transaction_id})
        if not transaction:
            return {'message': "A transaction with that ID does not exist in the database", 'code': 1}
        if not receiver_type:
            return {'message': "The Receiver Type was not specified", 'code': 1}
        if not amount:
            return {'message': "Invalid amount", 'code': 1}

        configuration = self.get_configuration({'shortcode': transaction.shortcode})
        if not configuration:
            return {'message': "The associated shortcode configuration does not exist", 'code': 1}
        credentials = ShortcodeInstanceCredentials(configuration)
        api_url = "https://sandbox.safaricom.co.ke/mpesa/reversal/v1/request"
        headers = {"Authorization": "Bearer %s" % credentials.access_token()}
        data = {
            "Initiator": credentials.initiator,
            "SecurityCredential": credentials.security_credential,
            "CommandID": "TransactionReversal",
            "TransactionID": transaction_id,
            "Amount": amount,
            "ReceiverParty": credentials.shortcode,
            "RecieverIdentifierType": receiver_type,
            "ResultURL": HOST + "/lipa/reversal/result",
            "QueueTimeOutURL": HOST + "/lipa/timeout",
            "Remarks": "Refund for " + order,
            "Occasion": "Odoo POS"
        }
        response = requests.post(api_url, json=data, headers=headers)
        if response.status_code != 200:
            return {"message": "The reversal request could not be processed", "code": 1}
        return {"message": "Processing request", "code": -1}

    @http.route('/lipa/simulate/status', type='json', auth='user', website=True)
    def payment_status(self, **kwargs):
        ref = kwargs.get("ref", False)
        trans_id = kwargs.get("trans_id", False)
        if ref and self.get_transaction({'reference': ref}):
            return {"message": self.customized_message(ref), "code": 0}
        message = self.get_transaction_status_message(trans_id, ref)
        if message:
            return {"message": message, "code": 0}

        return {"code": 1, "message": "Could not validate payment"}

    @http.route('/lipa/reversal/status', type='json', auth='user', website=True)
    def reversal_status(self, **kwargs):
        ref = kwargs.get("ref", False)
        trans_id = kwargs.get("trans_id", False)
        if trans_id and self.get_transaction({'reference': trans_id}):
            ref = f'{trans_id}, {ref}'
            transaction = self.get_transaction({"reference": trans_id})
            transaction.write({"reference": ref})
            return {"message": self.customized_message(ref), "code": 0}
        return {"code": 1, "message": "The reversal request could not be processed"}

    def check_transaction_status(self, trans_id, indentifier):
        if trans_id and indentifier:
            self.run_status_request(trans_id, indentifier)
            return {"message": "Processing request", "code": -1}
        return {"message": "Missing TransactionID or IndentifierType", "code": 1}
