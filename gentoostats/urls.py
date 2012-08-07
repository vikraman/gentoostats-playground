from django.conf.urls import patterns, include, url

# Django admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url( r'^upload/?'
       , include( 'gentoostats.receiver.urls'
                , namespace = 'receiver'
                , app_name  = 'receiver'
         )
    ),

    url( r'^'
       , include( 'gentoostats.stats.urls'
                , namespace = 'stats'
                , app_name  = 'stats'
         )
    ),
)
