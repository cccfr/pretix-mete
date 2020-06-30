from pretix.base.payment import BasePaymentProvider, PaymentException
from pretix.base.settings import SettingsSandbox
from pretix.base.models import Event, Order, OrderPayment, OrderRefund, Quota
from pretix.base.payment import PaymentException
from django.http import HttpRequest
from django import forms

from collections import OrderedDict
from urllib.parse import urlencode
import requests
import logging

class Mete(BasePaymentProvider):
    identifier = 'mete'
    verbose_name = 'Mete'
    payment_form_fields = OrderedDict([
    ])

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox('payment', 'mete', event)
        self.logger = logging.getLogger("Mete-Provider")
        
    @property
    def settings_form_fields(self):
      return OrderedDict(
        list(super().settings_form_fields.items()) + [
            ('meteserver',
             forms.CharField(
                 widget=forms.Textarea,
                 label='Mete Server',
                 required=True
             )),
             ('meteuser',
             forms.CharField(
                 widget=forms.Textarea,
                 label='Mete User',
                 required=True
             ))
        ]
    )
    
    def checkout_prepare(self, request, cart):
        res = requests.get("%s/drinks/" %(request.event.settings.payment_mete_meteserver))
        if res.status_code != 200:
            # TODO: add error message via django message framework
            return False
        else:
            return True

    @property
    def abort_pending_allowed(self):
        return False

    def checkout_confirm_render(self, request) -> str:
        """
        Returns the HTML that should be displayed when the user selected this provider
        on the 'confirm order' page.
        """
        # TODO: render nice html
        return "this order will appear on the Mete pad so you (or someone else) can pay for it)"

    def payment_is_valid_session(self, request):
        return True

    def payment_prepare(self, request: HttpRequest, payment: OrderPayment):
        return True

    def execute_payment(self, request: HttpRequest, payment: OrderPayment):
        item = {
                "name": "~SL~ %s#%s~%s" %(payment.order.event.slug, payment.order.code, payment.local_id),
                "caffeine": 0,
                "alcohol": 0,
                "energy": 0,
                "sugar": 0,
                "price": payment.amount,
                "image": 0,
                "active": True
                }
        params = self.prepare_params(item, "drink")
        self.logger.info("sending order to mete:\n%s" %params)
        res = requests.post("%s/api/v1/%s" %(request.event.settings.payment_mete_meteserver, "drinks"), params=params, headers={'Content-Type': 'application/json'})
        if res.status_code != 201:
            # TODO more verbose error logging
            self.logger.error("error posting the order to mete:\nreturncode: %s\nparams:%s\nserver response\n%s" %(res.status_code, params, res.text))
            raise PaymentException
        res = requests.patch("%s/api/v1/%s/%s" %(request.event.settings.payment_mete_meteserver, "drinks", res.json()["id"]), params=params, headers={'Content-Type': 'application/json'})
        if res.status_code != 204:
            # TODO more verbose error logging
            self.logger.error("error posting the price to mete:\nreturncode: %s\nparams:%s\nserver response\n%s" %(res.status_code, params, res.text))
            raise PaymentException

    def cancel_payment(self, payment: OrderPayment):
        items = requests.get("%s/api/v1/%s" %(meteserver, "drinks")).json()
        for drink in drinks:
            if "~SL~ %s#%s~%s" %(payment.order.event.name, payment.order.code, payment.local_id) in drink["name"]:
                requests.delete("%s/api/v1/%s/%s" %(request.event.settings.payment_mete_meteserver, "drinks", drink["id"]))

    def prepare_params(self, item, kind):
        params = {}
        for key in item.keys():
            params[kind+"["+key+"]"] = item[key]
        return urlencode(params)

