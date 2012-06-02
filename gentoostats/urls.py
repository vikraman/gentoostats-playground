from django.conf.urls import patterns, include, url

# Django admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/',     include(admin.site.urls)),

    url(r'^receive/',   include('gentoostats.receiver.urls')),
    url(r'^stats/',     include('gentoostats.stats.urls')),
    url(r'^',           include('gentoostats.main.urls')),
)
