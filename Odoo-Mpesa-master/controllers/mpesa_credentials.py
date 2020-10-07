import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64

HOST = "https://a5b2fcd3dbcb.ngrok.io"


class ShortcodeInstanceCredentials:
    def __init__(self, configuration):
        self.consumer_key = configuration['consumer_key']
        self.initiator = configuration["initiator"]
        self.security_credential = configuration["security_credential"]
        self.consumer_secret = configuration['consumer_secret']
        self.shortcode = str(configuration['shortcode'])
        self.passkey = configuration['pass_key']

    def access_token(self):
        api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
        r = requests.get(api_URL, auth=HTTPBasicAuth(self.consumer_key, self.consumer_secret))
        if r.status_code == 200:
            mpesa_access_token = json.loads(r.text)
            return mpesa_access_token['access_token']
        return False

    def online_password(self):
        lipa_time = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = self.shortcode + self.passkey + lipa_time
        password = base64.b64encode(data_to_encode.encode())
        return password.decode('utf-8')

    def register_urls(self):
        access_token = self.access_token()
        if not access_token:
            return False
        api_url = "https://sandbox.safaricom.co.ke/mpesa/c2b/v1/registerurl"
        headers = {"Authorization": "Bearer %s" % access_token}
        options = {"ShortCode": self.shortcode,
                   "ResponseType": "Completed",
                   "ConfirmationURL": HOST + "/lipa/confirm",
                   "ValidationURL": HOST + "/lipa/validate"
                   }
        response = requests.post(api_url, json=options, headers=headers)
        print(response.json())
        return response.status_code == 200
