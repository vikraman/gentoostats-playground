from django.conf.urls import patterns, include, url

# Django admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url( r'^admin/doc/'
       , include('django.contrib.admindocs.urls')
    ),

    url( r'^admin/'
       , include(admin.site.urls)
    ),

    url( r'^upload/?'
       , include( 'gentoostats.receiver.urls'
                , namespace = 'receiver'
                , app_name  = 'receiver'
         )
    ),

    url( r'^stats/'
       , include( 'gentoostats.stats.urls'
                , namespace = 'stats'
                , app_name  = 'stats'
         )
    ),

    url( r'^'
       , include( 'gentoostats.main.urls'
                , namespace = 'main'
                , app_name  = 'main'
         )
    ),
)
