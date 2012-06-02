from django.conf.urls import patterns, include, url

urlpatterns = patterns('gentoostats.stats.views',
    url(r'^host/(?P<host_id>\w+)/$', 'hostdetails',  name='hostdetails'),
    url(r'^$',                       'overallstats', name='overallstats'),
)
