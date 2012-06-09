from django.conf.urls import patterns, include, url

# Django admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('gentoostats.receiver.views',
    # NOTE: APPEND_SLASH's redirect may lead to loss of POST data.

    url(r'^/?$', 'process_submission', name='upload_url'),
)
