odoo.define("odoo_mpesa.paybillValidate", function(require) {
    "use strict";
    const Screens = require("point_of_sale.screens");
    const OrderView = require("point_of_sale.chrome");
    const core = require("web.core");

    Screens.PaymentScreenWidget.include({
        confirm_order:function(order){
            this.continue_validation(order);
            toggle_buttons();
        },
        cancel_order:function(order){
            const order_id = order.name.slice(6);
            localStorage.removeItem(order_id);
            toggle_buttons();
            this.renderElement();
        },
        renderElement: function() {
            let self = this;
            this._super();

            this.$(".confirm-button").click(function (){
                let order = self.pos.get_order();
                self.confirm_order(order);
            });
            this.$(".cancel-button").click(function (){
                let order = self.pos.get_order();
                self.cancel_order(order);
            });

        },

        // Get the paymentline whose payment method is mpesa
        get_mpesa_line:function(order){
            let lines = order.get_paymentlines();
            let count = 0;
            let mpesa_line = null;
            for(let i=0; i<lines.length;i++){
                let line = lines[i]
                if(line.payment_method.name.toLowerCase().trim() === "mpesa"){
                    mpesa_line = line;
                    count += 1;
                }
            }
            if(count) return {amount:mpesa_line.amount,count}
            return false
        },
        // Remove paymentlines with amount less than than or equal to zero before printing receipt
        clear_unused_payment_lines:function(order){
            let lines = order.get_paymentlines();
            for(let i=0;i<lines.length;i++){
                let line = lines[i]
                if(line.amount === 0) {
                    order.remove_paymentline(line);
                }
            }
            this.reset_input();
            this.renderElement();
        },

        payment_method_exists: function(order,payment_method){
            let lines = order.get_paymentlines();
            let payment_methods = [];
            for(let i=0;i<lines.length;i++){
                let line = lines[i]
                payment_methods.push(line.payment_method)
            }
            return payment_methods.includes(payment_method)
        },

        click_paymentmethods: function(id) {
            var payment_method = this.pos.payment_methods_by_id[id];
            var order = this.pos.get_order();

            if (order.electronic_payment_in_progress()) {
                this.gui.show_popup('error',{
                    'title': _t('Error'),
                    'body':  _t('There is already an electronic payment in progress.'),
                });
            } else {
                // Check whether payment method is already selected before adding a new paymentline
                if(!this.payment_method_exists(order,payment_method)){
                    order.add_paymentline(payment_method);
                    this.reset_input();
                }
                this.payment_interface = payment_method.payment_terminal;
                if (this.payment_interface) {
                    order.selected_paymentline.set_payment_status('pending');
                }

                this.render_paymentlines();
            }
        },
        // Extending the validation process to cater for Mpesa payment validation
        finalize_validation: function() {
            const order = this.pos.get_order();
            this.clear_unused_payment_lines(order);
            if (order.is_paid_with_cash() && this.pos.config.iface_cashdrawer) {

                this.pos.proxy.printer.open_cashbox();
            }
            order.initialize_validation_date();

            // Validate mpesa payment before finalizing order
            let mpesa_line = this.get_mpesa_line(order);
            if (mpesa_line && mpesa_line.count === 1) {
                let amount = mpesa_line.amount
                if(amount < 0){
                    this.initiate_refund(order, amount);
                }else{
                    this.simulate_mpesa_payment(order, amount);
                }
            }else if(mpesa_line.count > 1){
                this.gui.show_popup("error", {
                    title: "Validation Failed!",
                    body: "Only one Mpesa payment line is allowed",
                });
            }else{
                this.continue_validation(order)
            }
        },
        continue_validation: function (order){
            let self = this
            order.finalized = true;
            if (order.is_to_invoice()) {
                const invoiced = this.pos.push_and_invoice_order(order);
                this.invoicing = true;

                invoiced.catch(this._handleFailedPushForInvoice.bind(this, order, false));

                invoiced.then(function (server_ids) {
                    self.invoicing = false;
                    let post_push_promise = [];
                    post_push_promise = self.post_push_order_resolve(order, server_ids);
                    post_push_promise.then(function () {
                        self.gui.show_screen('receipt');
                    }).catch(function (error) {
                        self.gui.show_screen('receipt');
                        if (error) {
                            self.gui.show_popup('error',{
                                'title': "Error: no internet connection",
                                'body':  error,
                            });
                        }
                    });
                });
            } else {
                const ordered = this.pos.push_order(order);
                if (order.wait_for_push_order()){
                    let server_ids = [];
                    ordered.then(function (ids) {
                        server_ids = ids;
                    }).finally(function() {
                        let post_push_promise = [];
                        post_push_promise = self.post_push_order_resolve(order, server_ids);
                        post_push_promise.then(function () {
                            self.gui.show_screen('receipt');
                        }).catch(function (error) {
                            self.gui.show_screen('receipt');
                            if (error) {
                                self.gui.show_popup('error',{
                                    'title': "Error: no internet connection",
                                    'body':  error,
                                });
                            }
                        });
                    });
                }
                else {
                    self.gui.show_screen('receipt');
                }

            }
        },
        // display the appropriate message to the user based on the server's response'
        handle_response: function(data,order) {
            this.exit_validation_mode();
            const code = data["code"];
            const message = data["message"];
            const self = this;
            if (code === 0) {
                let order_id = order.name.slice(6);
                localStorage.setItem(order_id,message);
                display_confirmation_message(order_id)
            } else {
                self.gui.show_popup("error", {
                    title: "Validation Failed!",
                    body: message,
                });
            }
        },

        // Initialize mpesa simulate request
        simulate_mpesa_payment: function(order,amount) {
            const self = this;
            const order_id = order.name.slice(6);
            if(!display_confirmation_message(order_id)){
                const ref = order.name;
                const client = this.pos.get_client();
                const trans_id = client ? client.phone : prompt("Please select a customer or input the customer's phone number to validate Mpesa payment.");
                if(trans_id) {
                    const ajax = require("web.ajax");
                    ajax.jsonRpc(
                        "/lipa/simulate",
                        "call", {
                            indentifier:"4",
                            trans_id,
                            ref: ref,
                            amount: Math.round(amount),
                        },
                        this.enter_validation_mode()
                    )
                        .then(function (data) {
                            const code = data["code"];
                            if (code === 0 || code === 1) {
                                self.handle_response(data, order);
                            } else {
                                setTimeout(function () {
                                    self.check_request_status(order,trans_id,"/lipa/simulate/status",2)
                                }, 1000);
                            }
                        }).catch(function (error) {
                        self.exit_validation_mode();
                        if (error) {
                            self.gui.show_popup("error", {
                                title: "Ops! something went wrong",
                                body: error,
                            });
                        }
                    });
                }
            }else{
                this.continue_validation(order);
                $(".pos .button.next").removeClass("confirm")
                localStorage.removeItem(order_id);
            }
        },

        // Refund request Handler. Fired when the amount to paid is negative
        initiate_refund:function(order,amount){
            const self = this;
            const order_id = order.name.slice(6);
            if(!display_confirmation_message(order_id)){
                const receiver_type ="11";
                const transaction_id = prompt("Negative amount implies refund. " +
                    "Please enter the transaction ID for which you would like to initiate refund");
                if(transaction_id) {
                    const ajax = require("web.ajax");
                    ajax.jsonRpc(
                        "/lipa/reversal",
                        "call", {
                            receiver_type,
                            transaction_id,
                            amount: Math.abs(Math.round(amount)),
                            order:order.name
                        },
                        this.enter_validation_mode()
                    )
                        .then(function (data) {
                            const code = data["code"];
                            if (code === 0 || code === 1) {
                                self.handle_response(data, order);
                            } else {
                                setTimeout(function () {
                                    self.check_request_status(order,transaction_id,"/lipa/reversal/status",2)
                                }, 1000);
                            }
                        }).catch(function (error) {
                        self.exit_validation_mode();
                        if (error) {
                            self.gui.show_popup("error", {
                                title: "Ops! something went wrong",
                                body: error,
                            });
                        }
                    });
                }
            }else{
                this.continue_validation(order);
                $(".pos .button.next").removeClass("confirm")
                localStorage.removeItem(order_id);
            }
        },

        // Make ajax calls for the passed number of retries o check if payment
        check_request_status: function(order,trans_id,url,retries) {
            const self = this;
            const ref = order.name;
            const ajax = require("web.ajax");
            ajax.jsonRpc(
                    url,
                    "call", {trans_id, ref},
                    self.enter_validation_mode()
                )
                .then(function(data) {
                    if (data["code"] !== 0 && retries > 0) {
                        setTimeout(function(){self.check_request_status(order,trans_id,url,retries-1)},2000)
                    } else {
                        self.handle_response(data,order);
                    }
                }).catch(function(error) {
                self.exit_validation_mode();
                if (error) {
                    self.gui.show_popup("error", {
                        title: "Ops! something went wrong",
                        body: error,
                    });
                }
            });
        },

        enter_validation_mode: function() {
            $(".pos .button.next").addClass("loading")
        },
        exit_validation_mode: function() {
            $(".pos .button.next").removeClass("loading")
        },
    });

    OrderView.OrderSelectorWidget.include({
        order_click_handler: function(event,$el) {
            const order = this.get_order_by_uid($el.data('uid'));
            if (order) {
                this.pos.set_order(order);
                // Remember mpesa validation
                display_confirmation_message($el.data('uid'))
            }
        },
    })

// Show mpesa confirmation message if the payment has already been validated
function display_confirmation_message(order_id){
    const message = localStorage.getItem(order_id);
    if(message === null){
        return false
    }else{
        const selected_order = $(".select-order.selected");
        if (selected_order.attr("data-uid") === order_id){
            const container = $(".paymentlines-container");
            container.prepend(`<p class="confirmation-text">${message}</p>`)
            toggle_buttons();
        }
        return true
    }
}
function toggle_buttons(){
    let button1 = $(".pos .button.next");
    let button2 = $(".pos .button.confirm-view")
    if (button1.hasClass("hidden")){
        button1.removeClass("hidden");
        button2.addClass("hidden");
    }else{
        button1.addClass("hidden");
        button2.removeClass("hidden");
    }
}
});