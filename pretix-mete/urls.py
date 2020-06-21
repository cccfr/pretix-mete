from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^control/organizer/(?P<organizer>[^/]+)/mete/pay/',
        views.Pay.as_view(),
        name='pay'),
]