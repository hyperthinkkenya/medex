# Odoo Mpesa 

## This module integrates Odoo 13 POS with Mpesa
**NOTE:** The module currently works in **Kenya** only

![Logo](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601978344/Odoo-mpesa_hxbfik.png)

This module extends Odoo Point of Sale enabling you to validate and confirm, in real time, payments made through Mpesa by your customers. It also keeps record of all payments made via mpesa along with the particular order number associated with each payment for future reference. Moreover, it allows you to invoke refund right from the Odoo Point of Sale interface.

### Prerequisite

Please take note of the following before you proceed:
- You need a functional paybill/till number. 
- You should have ccess to your MPESA Web Portal which is only accessed using a certificate Safaricom offers you. Refer to this YouTube video on how to apply and install the Mpesa certificate: https://www.youtube.com/watch?v=wQyBkJDsmuw
- Also you need to register for a Safaricom developer's account if you don't have one. Here is the link: https://developer.safaricom.co.ke/
 
 
### Setup guide
1. Download/clone the module and add it to your Odoo instance as a custom addon
2. open the mpesa_credentials.py file(located inside the controllers folder) and change the value of the HOST variable to 
  match the URL on which your Odoo insance is running. The URL should be a publicly accessible domain/IP.

![Update HOST Variable](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601978344/host_jzrdpn.png)

3. Install or upgrade the module if it is already installed.
4. Configure your credentials as explained below

#### Configuring your credentials
+ With the module installed, select *Odoo mpesa* from the main menu then click on configuration
+ Click on 'create' 
+ Enter your credentials and save. **Note:** The configuration credentials will only be saved if they are correct, otherwise an error will be thrown

![Add configuration](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601978343/conf_uljyrb.png)

- For testing purposes, you can get the testing credentials from the Safaricom developer portal (https://developer.safaricom.co.ke/test_credentials)
- Navigate to *Point of sale > configuration > payment methods* 

![Open Payment methods settings](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601978344/navigate-to-payment-method_dbrxoo.png)

- Add a new payment method and name it **Mpesa** (Letter case doesn't matter)

![Add Mpesa payment method](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601978344/new_payment_method_lpadrv.png)

- Open the POS settings 

![Open POS Settings](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601978345/open-pos-settings_xnitws.png)

- Include Mpesa as one of the Payment methods

![Select Mpesa as one of payment methods](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601978345/selcect-payment-methods_uuxlwr.png)

#### How it works
- Once you are done with the setup, open Point of sale and start a new session.
- Select the products to sell and proceed to the payment page. 
- select Mpesa as the payment method then click on *Validate* button
- If no customer is selected, you will be prompted to provide either the client's phone number or the transaction ID.
- Enter any of the two and click *OK* or press *Enter key*
- The validation process will begin immediately. Wait for the validation process to finish
- If a matching record is found, a confirmation message will be displayed. You can accept the payment or cancel. Accepting payment finalizes the order and takes you to the receipt page where you can print the receipt
- If a customer is selected, the selected customer's phone number is used to conduct the validation.
- If no record was found, the validation fails and a poup with the text "Could not validate payment" is displayed.
- Incase of an error or internet failure, a popup with the the appropriate error message is displayed. 


Here is a quick demo: https://youtu.be/HvVSxbka4W0

[![How it works](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601981654/demo_thumbnail_y3vbbi.png)](https://youtu.be/HvVSxbka4W0)

#### Mpesa Payments Record

![payment records](https://res.cloudinary.com/da3jmmlpj/image/upload/v1601982437/records_v1ewcu.png)
