from django.conf.urls import patterns, include, url

# Django admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('gentoostats.receiver.views',
    url(r'^', 'receive', name='receive'),
)
