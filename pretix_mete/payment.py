from pretix.base.payment import BasePaymentProvider, PaymentException
from pretix.base.settings import SettingsSandbox
from pretix.base.models import Event, Order, OrderPayment, OrderRefund, Quota
from django import forms

from collections import OrderedDict
from urllib.parse import urlencode
import requests

class Mete(BasePaymentProvider):
    identifier = 'mete'
    verbose_name = 'Mete'
    payment_form_fields = OrderedDict([
    ])

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox('payment', 'mete', event)
        
    @property
    def settings_form_fields(self):
      return OrderedDict(
        list(super().settings_form_fields.items()) + [
            ('meteserver',
             forms.CharField(
                 widget=forms.Textarea,
                 label=_('Mete Server'),
                 required=True
             )),
             ('meteuser',
             forms.CharField(
                 widget=forms.Textarea,
                 label=_('Mete User'),
                 required=True
             ))
        ]
    )
    
    def checkout_prepare(self, request, cart):
        res = requests.get("http://%s/drinks/" %(request.event.settings.payment_mete_meteserver))
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

    def execute_payment(self, request: HttpRequest, payment: OrderPayment):
        item = {
                "name": "Schwarze Lunge #"+payment.Order.code,
                "caffeine": 0,
                "alcohol": 0,
                "energy": 0,
                "sugar": 0,
                "price": payment.amount,
                "image": 0,
                "active": true
                }
        params = prepare_params(item, "drink")
        res = requests.post("%s/api/v1/%s" %(request.event.settings.payment_mete_meteserver, "drinks"), params=params, headers={'Content-Type': 'application/json'})
        if res.status_code != 200:
            # TODO more verbose error logging
            raise
        
    def prepare_params(item, kind):
        params = {}
        for key in item.keys():
            params[kind+"["+key+"]"] = item[key]
        return urlencode(params)

